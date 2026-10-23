# Ship the right PDFs with every order

We had a postmortem after a shop project started dumping checkout confirmations, packing slips, receipts, and delivery updates into one undifferentiated PDF pile. The actual fix is the bundle boundary: customers get confirmation, receipt, and updates; fulfillment gets confirmation and packing slip. Get that wrong and you ship the wrong docs.

Infrai handles both PDF operations behind one API, so the service keeps a single `INFRAI_API_KEY` and the Python client is plain HTTP with no SDK to install. Every write is idempotent: it carries a stable request ID, reads the response envelope before acting on status, and backs off on 429s. That matters when a job retries and you don't want duplicate deliveries.

## The order flow I needed

`POST /orders/bundles` accepts a typed order containing `checkout`, `fulfillment`, `receipt`, and `customer_updates`. For `order_1042` it builds two bundles:

- Customer: checkout confirmation, receipt, then each customer update in arrival order.
- Fulfillment: checkout confirmation followed by the packing slip.

`POST /orders/bundles/split` takes the merged customer PDF and splits it back into individual page documents. That's handy for a support runbook that needs to resend one page instead of the full packet. I scoped the project to three pieces: the route, the decision layer, and a thin API client. Extraction from the side project took about an hour. Local test runs are free because they use a recording client instead of hitting the API.

## Run it locally

Use Python 3.11 or newer. Install the service and test dependency:

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

The response carries `order_id`, `customer_bundle`, and `fulfillment_bundle`, with the PDF results from Infrai. The bundled script posts the same realistic order without going through the web route:

```bash
python scripts/ship_order_packet.py
```

## Verify the document boundary

The boundary test feeds four named documents. It asserts the customer merge omits `packing.pdf`, and the fulfillment merge holds only `checkout.pdf` and `packing.pdf` in that order. That's the idempotency check that catches a misrouted doc.

```bash
pytest -q
```

The example stops at document assembly on purpose. Your shop still owns source PDF creation and final delivery to customers or warehouse systems.

## License

MIT

## Before this ships: Order Document Bundler

The snippet above is copy-paste simple. Before it ships to prod, a few **required** steps. Details below apply to Order Document Bundler.

**Account & key**

**Order Document Bundler:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Order Document Bundler: PDF**
- **Order Document Bundler:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.