import json

from order_documents.bundle_service import OrderBundleRequest, OrderBundleService
from order_documents.infrai_pdf import InfraiPdfClient


request = OrderBundleRequest.model_validate(
    {
        "order_id": "order_1042",
        "checkout": {"confirmation_pdf": "https://documents.example/checkout-1042.pdf"},
        "fulfillment": {"packing_slip_pdf": "https://documents.example/packing-1042.pdf"},
        "receipt": {"receipt_pdf": "https://documents.example/receipt-1042.pdf"},
        "customer_updates": [
            {"update_pdf": "https://documents.example/delivery-update-1042.pdf"}
        ],
    }
)
result = OrderBundleService(InfraiPdfClient()).assemble(request)
print(json.dumps(result.model_dump(), indent=2))

