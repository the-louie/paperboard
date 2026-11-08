"""Emulated TRMNL device: setup -> display -> image -> log, with the firmware's real headers.

Header set and behaviour from usetrmnl/firmware 5246feb (1.8.19) per the research notes and
the owner's device as seen on byos-host (T-04): a single 307/308 redirect is followed, a 302 is
a failure, gzip is refused, and ID/Access-Token go to the image URL only on the same origin.

Library use (tests): FakeTrmnl(session, base="") where session has aiohttp-style
get()/post() (aiohttp.ClientSession or HA's test client).
CLI: python scripts/fake_trmnl.py http://host:port [--mac AA:..] [--key KEY]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

FW_VERSION = "1.8.10"
MODEL = "xiao_epaper_display"


class FirmwareError(Exception):
    """Something the real firmware would reject."""


@dataclass
class FakeTrmnl:
    session: Any
    base: str = ""
    mac: str = "02:00:00:00:00:01"  # locally administered, never a real device
    api_key: str | None = None
    friendly_id: str | None = None
    battery_v: str = "4.20"
    rssi: str = "-56"
    refresh_rate: str = "900"
    cached: list[str] = field(default_factory=list)
    last_image: bytes = b""

    def _common(self) -> dict[str, str]:
        return {"ID": self.mac, "Content-Type": "application/json", "FW-Version": FW_VERSION,
                "Model": MODEL, "Width": "800", "Height": "480", "RSSI": self.rssi,
                "Accept-Encoding": "identity"}

    def display_headers(self) -> dict[str, str]:
        return {**self._common(), "Access-Token": self.api_key or "", "Update-Source": "timer",
                "Refresh-Rate": self.refresh_rate, "Battery-Voltage": self.battery_v,
                "Image-Cached": "true" if self.cached else "false", "Wake-Time": "5374",
                "Reset-Reason": "ESP_RST_DEEPSLEEP", "Temperature-Profile": "true",
                "Log-Level": "info", "WiFi-Band": "2.4"}

    async def _get(self, url: str, headers: dict[str, str]) -> tuple[int, dict, bytes]:
        for hop in range(2):
            resp = await self.session.get(url, headers=headers, allow_redirects=False)
            body = await resp.read()
            if resp.headers.get("Content-Encoding"):
                raise FirmwareError(f"gzip/compressed response from {url}")
            if resp.status in (307, 308) and hop == 0:
                url = resp.headers["Location"]
                continue
            if resp.status in (301, 302, 303, 307, 308):
                raise FirmwareError(f"redirect {resp.status} not followed by firmware")
            return resp.status, dict(resp.headers), body
        raise FirmwareError("second redirect")

    async def setup(self) -> dict[str, Any]:
        status, _, body = await self._get(f"{self.base}/api/setup", self._common())
        data = json.loads(body)
        if status != 200 or data.get("status") != 200:
            return data
        self.api_key, self.friendly_id = data["api_key"], data["friendly_id"]
        return data

    async def display(self) -> dict[str, Any]:
        _, _, body = await self._get(f"{self.base}/api/display", self.display_headers())
        data = json.loads(body)
        if data.get("status") == 500:
            self.api_key = None  # firmware drops its key and re-runs setup
        return data

    async def fetch_image(self, image_url: str) -> tuple[int, bytes]:
        same_origin = urlsplit(image_url).netloc in ("", urlsplit(self.base).netloc)
        headers = {"Accept-Encoding": "identity"}
        if same_origin:
            headers |= {"ID": self.mac, "Access-Token": self.api_key or ""}
        status, _, body = await self._get(image_url, headers)
        if status == 200:
            self.last_image = body
        return status, body

    async def log(self, message: str) -> int:
        payload = {"logs": [{"created_at": 0, "id": 1, "message": message,
                             "firmware_version": FW_VERSION, "battery_voltage": self.battery_v,
                             "wifi_signal": int(self.rssi), "level": "info"}]}
        headers = {"ID": self.mac, "Access-Token": self.api_key or "", "Accept": "*/*",
                   "Content-Type": "application/json", "Accept-Encoding": "identity"}
        resp = await self.session.post(f"{self.base}/api/log", headers=headers,
                                       data=json.dumps(payload))
        await resp.read()
        return resp.status

    async def cycle(self) -> dict[str, Any]:
        """One wake: setup if needed, display, fetch the image unless cached, log."""
        if not self.api_key:
            setup = await self.setup()
            if setup.get("status") != 200:
                return {"setup": setup}
        disp = await self.display()
        result: dict[str, Any] = {"display": disp}
        if disp.get("status") == 0 and disp.get("filename") not in self.cached:
            status, body = await self.fetch_image(disp["image_url"])
            result["image"] = {"status": status, "bytes": len(body)}
            if status == 200:
                self.cached = [disp["filename"], *self.cached][:30]
        result["log"] = await self.log("fake_trmnl cycle")
        return result


async def _main() -> None:
    import aiohttp

    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--mac", default="02:00:00:00:00:01")
    ap.add_argument("--key")
    args = ap.parse_args()
    async with aiohttp.ClientSession(auto_decompress=False) as session:
        dev = FakeTrmnl(session, base=args.base.rstrip("/"), mac=args.mac, api_key=args.key)
        print(json.dumps(await dev.cycle(), indent=1, default=str))


if __name__ == "__main__":
    asyncio.run(_main())
