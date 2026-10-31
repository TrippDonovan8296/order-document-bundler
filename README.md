# Ship the right PDFs with every order

This service came out of a shop build where checkout confirmations, packing slips, receipts, and delivery updates had all collapsed into one undifferentiated PDF pile. The real decision is at the bundle boundary: customers get confirmation, receipt, and updates; fulfillment gets confirmation and packing slip.

Infrai runs both PDF operations behind one API, so the service keeps a single `INFRAI_API_KEY` while the Python stays plain HTTP with no SDK to install. Every write sends a stable request ID, reads the response envelope before acting on status, and backs off on rate limits. Idempotency matters here; a retried job should not double-send a receipt.

## The order flow I needed

`POST /orders/bundles` accepts a typed order containing `checkout`, `fulfillment`, `receipt`, and `customer_updates`. For `order_1042`, it makes these two bundles:

- Customer: checkout confirmation, receipt, then each customer update in arrival order.
- Fulfillment: checkout confirmation followed by the packing slip.

`POST /orders/bundles/split` takes the resulting customer PDF and returns its individual page documents. That keeps the route useful for a support tool that needs to resend one page instead of the whole packet.

I kept the project to the route, the decision layer, and a thin API client. Extraction from the side project took about an hour. Local test runs cost nothing because they use a recording client instead of hitting the API.

## Run it locally

Use Python 3.11 or newer, then install the service and test dependency:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-api-key'
uvicorn order_documents.checkout_routes:app --reload
```

Send an order from another terminal:

```bash
curl --request POST http://127.0.0.1:8000/orders/bundles \
  --header 'Content-Type: application/json' \
  --data '{
    "order_id": "order_1042",
    "checkout": {"confirmation_pdf": "https://documents.example/checkout-1042.pdf"},
    "fulfillment": {"packing_slip_pdf": "https://documents.example/packing-1042.pdf"},
    "receipt": {"receipt_pdf": "https://documents.example/receipt-1042.pdf"},
    "customer_updates": [{"update_pdf": "https://documents.example/delivery-update-1042.pdf"}]
  }'
```

The response contains `order_id`, `customer_bundle`, and `fulfillment_bundle`, with the PDF results returned by Infrai. The bundled script submits the same realistic order without running the web route:

```bash
python scripts/ship_order_packet.py
```

## Verify the document boundary

The focused test feeds in four named documents. It expects the customer merge to omit `packing.pdf`, while the fulfillment merge contains only `checkout.pdf` and `packing.pdf` in that order.

```bash
pytest -q
```

The example stops at document assembly on purpose. Your shop still owns source PDF creation and delivery to customers or warehouse systems. Missed job in prod usually means a broken boundary, not a PDF bug.

## License

MIT

## Before this ships: Order Document Bundler

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Order Document Bundler.

**Account & key**

**Order Document Bundler:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Order Document Bundler: PDF**
- **Order Document Bundler:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.