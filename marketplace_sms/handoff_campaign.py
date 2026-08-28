from typing import Any

from .models import (
    BuyerUpdate,
    CampaignReceipt,
    CampaignRequest,
    CampaignStatus,
    MessageReceipt,
)


class HandoffCampaigns:
    def __init__(self, sms: Any) -> None:
        self.sms = sms

    def send(self, campaign: CampaignRequest) -> CampaignReceipt:
        self._reject_duplicate_orders(campaign.updates)
        receipts = []
        for update in campaign.updates:
            data = self.sms.send(
                to=update.buyer_phone,
                message=self._handoff_message(update),
                idempotency_key=f"{campaign.campaign_id}:{update.order_id}",
            )
            receipts.append(
                MessageReceipt(
                    order_id=update.order_id,
                    message_id=data["message_id"],
                    status=str(data.get("status", "queued")),
                )
            )
        return CampaignReceipt(campaign_id=campaign.campaign_id, messages=receipts)

    def refresh(self, receipt: CampaignReceipt) -> CampaignStatus:
        messages = []
        for sent in receipt.messages:
            data = self.sms.status(sent.message_id)
            messages.append(
                MessageReceipt(
                    order_id=sent.order_id,
                    message_id=sent.message_id,
                    status=str(data["status"]),
                )
            )
        complete = all(item.status in {"delivered", "failed"} for item in messages)
        return CampaignStatus(
            campaign_id=receipt.campaign_id,
            messages=messages,
            state="complete" if complete else "pending",
        )

    @staticmethod
    def _reject_duplicate_orders(updates: list[BuyerUpdate]) -> None:
        order_ids = [update.order_id for update in updates]
        if len(order_ids) != len(set(order_ids)):
            raise ValueError("Each order may appear once in a campaign")

    @staticmethod
    def _handoff_message(update: BuyerUpdate) -> str:
        return (
            f"Order {update.order_id}: {update.asset.title} is ready for handoff. "
            f"{update.asset.pickup_note}"
        )
