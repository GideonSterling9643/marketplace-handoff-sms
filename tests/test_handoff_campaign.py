import pytest

from marketplace_sms.handoff_campaign import HandoffCampaigns
from marketplace_sms.models import BuyerUpdate, CampaignRequest, SellerAsset


class RecordingSms:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, to: str, message: str, idempotency_key: str) -> dict:
        self.sent.append(
            {"to": to, "message": message, "idempotency_key": idempotency_key}
        )
        return {"message_id": f"msg-{len(self.sent)}", "status": "queued"}

    def status(self, message_id: str) -> dict:
        return {"message_id": message_id, "status": "delivered"}


def update(order_id: str, phone: str) -> BuyerUpdate:
    return BuyerUpdate(
        order_id=order_id,
        buyer_phone=phone,
        asset=SellerAsset(
            listing_id=f"listing-{order_id}",
            title="Walnut writing desk",
            pickup_note="Collect from the east entrance.",
        ),
    )


def test_campaign_keeps_order_handoffs_distinct_and_reports_completion() -> None:
    sms = RecordingSms()
    service = HandoffCampaigns(sms)
    receipt = service.send(
        CampaignRequest(
            campaign_id="handoff-friday",
            updates=[update("1042", "+15550000001"), update("1043", "+15550000002")],
        )
    )

    assert [call["idempotency_key"] for call in sms.sent] == [
        "handoff-friday:1042",
        "handoff-friday:1043",
    ]
    assert "Order 1042" in sms.sent[0]["message"]
    assert service.refresh(receipt).state == "complete"


def test_campaign_rejects_the_same_order_twice_before_sending() -> None:
    sms = RecordingSms()
    service = HandoffCampaigns(sms)

    with pytest.raises(ValueError, match="Each order may appear once"):
        service.send(
            CampaignRequest(
                campaign_id="handoff-friday",
                updates=[update("1042", "+15550000001"), update("1042", "+15550000001")],
            )
        )

    assert sms.sent == []
