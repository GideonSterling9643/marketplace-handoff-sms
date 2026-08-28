from typing import Literal

from pydantic import BaseModel, Field


class SellerAsset(BaseModel):
    listing_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    pickup_note: str = Field(min_length=1)


class BuyerUpdate(BaseModel):
    order_id: str = Field(min_length=1)
    buyer_phone: str = Field(min_length=1)
    asset: SellerAsset


class CampaignRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    updates: list[BuyerUpdate] = Field(min_length=1)


class MessageReceipt(BaseModel):
    order_id: str
    message_id: str
    status: str


class CampaignReceipt(BaseModel):
    campaign_id: str
    messages: list[MessageReceipt]


class CampaignStatus(BaseModel):
    campaign_id: str
    messages: list[MessageReceipt]
    state: Literal["pending", "complete"]
