from fastapi import FastAPI, HTTPException

from .bundle_service import (
    BundleResult,
    OrderBundleRequest,
    OrderBundleService,
    SplitBundleRequest,
    SplitResult,
)
from .infrai_pdf import InfraiError, InfraiPdfClient

app = FastAPI(title="Order document bundler")


def service() -> OrderBundleService:
    return OrderBundleService(InfraiPdfClient())


@app.post("/orders/bundles", response_model=BundleResult)
def build_order_bundles(request: OrderBundleRequest) -> BundleResult:
    try:
        return service().assemble(request)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc


@app.post("/orders/bundles/split", response_model=SplitResult)
def split_order_bundle(request: SplitBundleRequest) -> SplitResult:
    try:
        return service().split_customer_bundle(request)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc

