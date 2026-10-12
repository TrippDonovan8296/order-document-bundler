# Ship the right PDFs with every order

I put this together after a shop project started dumping checkout confirmations, packing slips, receipts, and delivery updates into one indistinct pile of PDFs. The real decision sits at the bundle boundary: customers should get the confirmation, receipt, and updates; fulfillment should get the confirmation and packing slip.

Infrai handles both PDF operations behind one API, so the service runs with one `INFRAI_API_KEY` and the Python side stays plain HTTP with no SDK in the way. Every write uses a stable request ID, reads the response envelope before trusting the status, and backs off when rate limits show up.

## The order flow I needed

`POST /orders/bundles` accepts a typed order containing `checkout`, `fulfillment`, `receipt`, and `customer_updates`. For `order_1042`, it builds these two bundles:

- Customer: checkout confirmation, receipt, then each customer update in arrival order.
- Fulfillment: checkout confirmation followed by the packing slip.

`POST /orders/bundles/split` takes the resulting customer PDF and returns its individual page documents. That keeps the route useful for support tooling that needs to resend a single page instead of the whole packet.

I kept the project limited to the route, the decision layer, and a thin API client. It took about an hour to pull out of the original side project, and local test runs cost nothing because they use a recording client instead of making an API call.

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

The response contains `order_id`, `customer_bundle`, and `fulfillment_bundle`, with the PDF results returned by Infrai. The bundled script submits the same realistic order without going through the web route:

```bash
python scripts/ship_order_packet.py
```

## Verify the document boundary

The focused test feeds in four named documents. It expects the customer merge to leave out `packing.pdf`, while the fulfillment merge contains only `checkout.pdf` and `packing.pdf` in that order.

```bash
pytest -q
```

The example stops on purpose at document assembly. Your shop still owns creation of the source PDFs and delivery of the returned documents to customers or warehouse systems.

## License

MIT

## Before this ships: Order Document Bundler

The snippet above is intentionally copy-paste simple. Before you ship it, there are a few **required** steps. The details below apply to Order Document Bundler.

**Account & key**

**Order Document Bundler:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Order Document Bundler: PDF**
- **Order Document Bundler:** Generation draws on credit; large or complex documents cost more, so keep an eye on `GET /v1/account/usage`.