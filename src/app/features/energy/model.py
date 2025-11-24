from pydantic import BaseModel


class ElectricityPriceRequest(BaseModel):
    VAT: float = 0.255
    fixed_unit_price: float = 8.96
    force_update: bool = False


class ElectricitySpotPrices(BaseModel):
    timestamp: int | None = None
    note: str | None = None
    price: float
