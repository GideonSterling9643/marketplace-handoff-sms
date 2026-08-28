import os

from marketplace_sms.handoff_campaign import HandoffCampaigns
from marketplace_sms.infrai_sms import InfraiSms
from marketplace_sms.models import BuyerUpdate, CampaignRequest, SellerAsset


phone = os.environ["DEMO_BUYER_PHONE"]
campaign = CampaignRequest(
    campaign_id="weekend-handoffs-001",
    updates=[
        BuyerUpdate(
            order_id="order-1042",
            buyer_phone=phone,
            asset=SellerAsset(
                listing_id="listing-88",
                title="Walnut writing desk",
                pickup_note="Meet the seller at the east entrance at 18:30.",
            ),
        )
    ],
)

receipt = HandoffCampaigns(InfraiSms()).send(campaign)
print(receipt.model_dump_json(indent=2))
