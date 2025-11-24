from logging import getLogger
from datetime import datetime, timedelta
from httpx import AsyncClient
from zoneinfo import ZoneInfo

from app.core.cache import cache_or_run_func
from .model import ElectricityPriceRequest

logger = getLogger("feature.energy")


class ElectricityService:
    """Handle electricity pricing and consumption logic"""

    async def get_spot_prices(self, request: ElectricityPriceRequest) -> dict:
        """Get Nordpool spot prices, with caching"""
        data = await cache_or_run_func(
            self.__retrieve_spot_prices,
            "spot_prices",
            force_update=request.force_update
        )
        
        if datetime.fromtimestamp(data[-1]["timestamp"]) < datetime.now() - timedelta(hours=2):
            logger.info("Spot prices are outdated, refreshing...")
            data = await cache_or_run_func(
                self.__retrieve_spot_prices,
                "spot_prices",
                force_update=True
            )

        for item in data:
            item["price"] = round((item["price"] * (1 + request.VAT) / 10), 2)  # €/MWh → ¢/kWh with VAT
            item["note"] = datetime.fromtimestamp(item["timestamp"]).strftime("%b%d %H:%M")

        return data

    async def __retrieve_spot_prices(self) -> dict:
        """Internal function to get Nordpool prices from remote"""

        async with AsyncClient() as client:
            response = await client.get((
                "https://dashboard.elering.ee/api/nps/price"
                f"?start={datetime.now()-timedelta(days=1):%Y-%m-%d}T20:59:59.999Z"
                f"&end={datetime.now()+timedelta(days=1):%Y-%m-%d}T23:59:59.999Z"
            ))
            response.raise_for_status()

        logger.info(f"GET elering.ee status: {response.status_code}")
        spot_prices_fi = response.json().get("data", {}).get("fi", [])
        logger.info((
            f"GET elering.ee result n={len(spot_prices_fi)}"
            f"{datetime.fromtimestamp(spot_prices_fi[0]['timestamp']):%b%d %H:%M}"
            f"{datetime.fromtimestamp(spot_prices_fi[-1]['timestamp']):%b%d %H:%M}"
        ))
        return spot_prices_fi

    async def render_spot_price_ascii(self, request: ElectricityPriceRequest):
        """Return (and optionally persist) an ASCII bar chart of quarter-hour spot prices."""

        max_bar_width: int = 40
        entries = await self.get_spot_prices(request)

        local_times = [
            datetime.fromtimestamp(item["timestamp"], tz=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Helsinki"))
            for item in entries
        ]
        prices = [item["price"] for item in entries]
        labels = [ts.strftime("%H:%M") if ts.minute == 0 else "" for ts in local_times]

        now_local = datetime.now(ZoneInfo("Europe/Helsinki"))
        slot_length = timedelta(minutes=15)
        current_idx = next(
            (idx for idx, ts in enumerate(local_times) if ts <= now_local < ts + slot_length),
            None,
        )

        max_price = max(prices)
        scale = max_bar_width / max_price if max_price else 1.0
        ref_index = min(max_bar_width - 1, max(0, int(round(request.fixed_unit_price * scale)) - 1))

        lines = ["Nordpool Quarter-Hour Prices (ASCII, Helsinki time)", "-" * 72]
        for idx, (label, price) in enumerate(zip(labels, prices)):
            bar_len = max(1, int(round(price * scale))) if price > 0 else 1
            fill_char = "█" if idx == current_idx else "░"
            bar = [" "] * max_bar_width
            for pos in range(bar_len):
                bar[pos] = fill_char
            bar[ref_index] = "│" if bar[ref_index] == " " else "┆"

            marker = "▶" if idx == current_idx else " "
            label_text = f"{label:>5}" if label else "     "
            show_value = current_idx == idx or local_times[idx].minute == 30
            arrow = "◀" if idx == current_idx else " "
            value_text = f"{arrow}{price:6.2f}" if show_value else "       "
            lines.append(f"{marker} {label_text} | {''.join(bar)}  {value_text}")

        ascii_output = "\n".join(lines)
        return ascii_output


electricity_service = ElectricityService()
