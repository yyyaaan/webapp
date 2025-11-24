from fastapi import APIRouter, Depends, responses
from logging import getLogger

from app.auth.security import require_user_or_api_key
from .model import ElectricitySpotPrices, ElectricityPriceRequest
from .service import ElectricityService, electricity_service

logger = getLogger("feature.energy")
router = APIRouter(dependencies=[Depends(require_user_or_api_key)])


@router.get("/spot-prices", response_model=list[ElectricitySpotPrices])
async def get_spot_prices(
    params: ElectricityPriceRequest = Depends(),
    service: ElectricityService = Depends(lambda: electricity_service),
):
    return await service.get_spot_prices(params)


@router.get("/spot-prices/plot", response_class=responses.PlainTextResponse)
async def plot_spot_prices(
    params: ElectricityPriceRequest = Depends(),
    service: ElectricityService = Depends(lambda: electricity_service),
):
    return await service.render_spot_price_ascii(params)
