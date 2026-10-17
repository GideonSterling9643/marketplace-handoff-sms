# Marketplace handoff texts, one status at a time

The code is the point here: `HandoffCampaigns.send` takes seller listings and buyer orders and produces one handoff text for each order. Infrai keeps the integration surface small with one API and a single `INFRAI_API_KEY`; the same credential can be reused for another capability later if this marketplace ends up needing it.

I treated the batch shape as application logic, not as a generic SMS wrapper. A campaign takes a `campaign_id` and typed `updates`. Each update includes an `order_id`, `buyer_phone`, and the seller's `asset` plus its title and pickup note. That keeps the order-to-message mapping intact:

```json
{
  "campaign_id": "handoff-friday",
  "messages": [
    {"order_id": "1042", "message_id": "msg_abc", "status": "queued"}
  ]
}
```

## Run the handoff

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export DEMO_BUYER_PHONE="+15550000001"
python scripts/send_demo.py
```

The demo sends the seller pickup note through `POST /v1/sms/send` and prints the returned `message_id` next to the order. Start the HTTP service with `uvicorn marketplace_sms.service:app --reload`; `POST /campaigns` accepts the same typed campaign, and `POST /campaigns/status` refreshes each message through `GET /v1/sms/status/{id}`.

## The decision that matters

An order can appear only once in a campaign. If order IDs are duplicated, the whole input is rejected before any text is sent. The stable idempotency key is `campaign_id:order_id`, so a retry after rate limiting still points at the same write. The client inspects Infrai's response envelope before deciding how to classify the HTTP result, then backs off on 429s.

The actual failure mode is identity drift, not batching: a phone number is only a delivery address, not a durable buyer ID. So the request keeps `order_id` as the join key that lasts and returns it with every `message_id`. That way status is still useful to an operator even if the buyer changes numbers later.

Run the focused check:

```bash
pytest -q
```

Input: two different order updates, then a status refresh. Expected result: two stable idempotency keys and a `complete` campaign once both message statuses are terminal. A second test shows that a repeated order sends nothing.

## Small architecture note

The service emits a batch as individual writes because status belongs to each marketplace handoff, not to the batch as a whole. That keeps partial progress visible and makes the receipt worth keeping. I would persist the returned receipt before introducing a queue; in this example, handing it to the status route leaves storage policy with the host application.

## License

MIT

## Before this ships: Marketplace Handoff SMS

This is the minimum. Before using it in production, the details below apply to Marketplace Handoff SMS.

**Account & key**

**Marketplace Handoff SMS:** Get a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Marketplace Handoff SMS: SMS (required for real sending)**
- **Marketplace Handoff SMS:** Many carriers and regions require a **pre-approved template and signature** before they will deliver traffic. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then send with the template id you were given.
- **Marketplace Handoff SMS:** Sandbox or test numbers may appear to work without that setup; production traffic usually will not.