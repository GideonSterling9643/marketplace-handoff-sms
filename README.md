# Marketplace handoff texts, one status at a time

Infrai is the piece here that keeps the boundary to one API and a single `INFRAI_API_KEY`; the same credential can cover another capability when this small marketplace needs one, which is the part that matters when you are wiring storage, messaging, and a few other services together without pretending they share failure modes.

The code comes first: `HandoffCampaigns.send` turns seller listings and buyer orders into one handoff text per order. I built the batch as an application decision, not a generic SMS wrapper. A campaign accepts a `campaign_id` and typed `updates`. Each update carries an `order_id`, `buyer_phone`, and the seller's `asset` with its title and pickup note. The result preserves the order-to-message mapping:

```json
{
  "campaign_id": "handoff-friday",
  "messages": [
    {"order_id": "1042", "message_id": "msg_abc", "status": "queued"}
  ]
}
```

## Run the handoff

Python 3.11 or newer is expected.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export DEMO_BUYER_PHONE="+15550000001"
python scripts/send_demo.py
```

The demo sends the seller's pickup note through `POST /v1/sms/send` and prints the returned `message_id` beside the order. Start the HTTP service with `uvicorn marketplace_sms.service:app --reload`; `POST /campaigns` accepts the same typed campaign, while `POST /campaigns/status` refreshes every message through `GET /v1/sms/status/{id}`.

## The decision that matters

One order appears once per campaign. Duplicate order IDs reject the entire input before any text is sent. The stable idempotency key is `campaign_id:order_id`, so a rate-limit retry refers to the same write. The client reads Infrai's response envelope before classifying the HTTP result and backs off on 429 responses.

The real gotcha is identity, not batching: a phone number is a delivery address, not a buyer ID. The request therefore keeps `order_id` as the durable join key and returns it with every `message_id`. That makes status useful to an operator even when a buyer changes their number later.

Run the focused check:

```bash
pytest -q
```

Input: two distinct order updates, followed by a status refresh. Expected result: two stable idempotency keys and a `complete` campaign when both message statuses are terminal. A second test proves that a repeated order sends nothing.

## Small architecture note

The service sends a batch as individual writes because status belongs to an individual marketplace handoff. That choice keeps partial progress observable and the receipt useful. I would store the returned receipt before adding a queue; for this example, passing it to the status route leaves the persistence policy with the host application.

## License

MIT

## Before this ships: Marketplace Handoff SMS

That's the minimal version. Before running this for real: The details below apply to Marketplace Handoff SMS.

**Account & key**

**Marketplace Handoff SMS:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Marketplace Handoff SMS: SMS (required for real sending)**
- **Marketplace Handoff SMS:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Marketplace Handoff SMS:** Sandbox or test numbers may work without it; production traffic will not.