from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class PdfOperations(Protocol):
    def merge(self, inputs: list[str], request_id: str) -> dict[str, Any]:
        raise AssertionError("Protocol method called directly")

    def split(self, pdf: str, ranges: list[str], request_id: str) -> dict[str, Any]:
        raise AssertionError("Protocol method called directly")


class CheckoutDocument(BaseModel):
    confirmation_pdf: str


class FulfillmentDocument(BaseModel):
    packing_slip_pdf: str


class ReceiptDocument(BaseModel):
    receipt_pdf: str


class CustomerUpdate(BaseModel):
    update_pdf: str


class OrderBundleRequest(BaseModel):
    order_id: str = Field(min_length=1)
    checkout: CheckoutDocument
    fulfillment: FulfillmentDocument
    receipt: ReceiptDocument
    customer_updates: list[CustomerUpdate] = Field(default_factory=list)


class BundleResult(BaseModel):
    order_id: str
    customer_bundle: dict[str, Any]
    fulfillment_bundle: dict[str, Any]


class SplitBundleRequest(BaseModel):
    order_id: str = Field(min_length=1)
    customer_bundle_pdf: str
    ranges: list[str]


class SplitResult(BaseModel):
    order_id: str
    pages: dict[str, Any]


class OrderBundleService:
    def __init__(self, pdf: PdfOperations) -> None:
        self._pdf = pdf

    def assemble(self, request: OrderBundleRequest) -> BundleResult:
        customer_inputs = [
            request.checkout.confirmation_pdf,
            request.receipt.receipt_pdf,
            *(item.update_pdf for item in request.customer_updates),
        ]
        fulfillment_inputs = [
            request.checkout.confirmation_pdf,
            request.fulfillment.packing_slip_pdf,
        ]
        return BundleResult(
            order_id=request.order_id,
            customer_bundle=self._pdf.merge(customer_inputs, f"{request.order_id}-customer"),
            fulfillment_bundle=self._pdf.merge(fulfillment_inputs, f"{request.order_id}-fulfillment"),
        )

    def split_customer_bundle(self, request: SplitBundleRequest) -> SplitResult:
        pages = self._pdf.split(request.customer_bundle_pdf, request.ranges, f"{request.order_id}-customer-pages")
        return SplitResult(order_id=request.order_id, pages=pages)
