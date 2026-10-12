from typing import Any

import httpx

from order_documents.bundle_service import OrderBundleRequest, OrderBundleService, SplitBundleRequest
from order_documents.infrai_pdf import InfraiPdfClient


class RecordingPdf:
    def __init__(self) -> None:
        self.merges: list[tuple[list[str], str]] = []
        self.splits: list[tuple[str, list[str], str]] = []

    def merge(self, inputs: list[str], request_id: str) -> dict[str, Any]:
        self.merges.append((inputs, request_id))
        return {"document": request_id}

    def split(self, pdf: str, ranges: list[str], request_id: str) -> dict[str, Any]:
        self.splits.append((pdf, ranges, request_id))
        return {"source": pdf, "request": request_id}


def test_customer_packet_excludes_warehouse_packing_slip() -> None:
    pdf = RecordingPdf()
    request = OrderBundleRequest.model_validate(
        {
            "order_id": "order_1042",
            "checkout": {"confirmation_pdf": "checkout.pdf"},
            "fulfillment": {"packing_slip_pdf": "packing.pdf"},
            "receipt": {"receipt_pdf": "receipt.pdf"},
            "customer_updates": [{"update_pdf": "delivery-update.pdf"}],
        }
    )

    result = OrderBundleService(pdf).assemble(request)

    assert pdf.merges == [
        (["checkout.pdf", "receipt.pdf", "delivery-update.pdf"], "order_1042-customer"),
        (["checkout.pdf", "packing.pdf"], "order_1042-fulfillment"),
    ]
    assert result.customer_bundle == {"document": "order_1042-customer"}


def test_split_passes_ranges_through_service_and_client() -> None:
    request = SplitBundleRequest(order_id="order_1042", customer_bundle_pdf="bundle.pdf", ranges=["1-2"])
    recording = RecordingPdf()
    OrderBundleService(recording).split_customer_bundle(request)
    assert recording.splits == [("bundle.pdf", ["1-2"], "order_1042-customer-pages")]

    def respond(sent: httpx.Request) -> httpx.Response:
        assert sent.url.path == "/v1/pdf/split"
        assert sent.headers["Idempotency-Key"] == "order_1042-customer-pages"
        assert sent.read() == b'{"pdf":"bundle.pdf","ranges":["1-2"]}'
        return httpx.Response(200, json={"ok": True, "data": {"pages": []}})

    client = InfraiPdfClient(api_key="test", transport=httpx.MockTransport(respond))
    assert client.split(request.customer_bundle_pdf, request.ranges, "order_1042-customer-pages") == {"pages": []}
