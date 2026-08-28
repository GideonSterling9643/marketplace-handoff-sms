from fastapi import FastAPI, HTTPException

from .handoff_campaign import HandoffCampaigns
from .infrai_sms import InfraiError, InfraiSms
from .models import CampaignReceipt, CampaignRequest, CampaignStatus


app = FastAPI(title="Marketplace handoff SMS")


def campaigns() -> HandoffCampaigns:
    return HandoffCampaigns(InfraiSms())


@app.post("/campaigns", response_model=CampaignReceipt)
def send_campaign(request: CampaignRequest) -> CampaignReceipt:
    try:
        return campaigns().send(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": exc.detail.get("message")},
        ) from exc


@app.post("/campaigns/status", response_model=CampaignStatus)
def campaign_status(receipt: CampaignReceipt) -> CampaignStatus:
    try:
        return campaigns().refresh(receipt)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": exc.detail.get("message")},
        ) from exc
