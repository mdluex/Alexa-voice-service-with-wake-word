"""Helpers for Amazon AVS config.json (official deviceInfo shape)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CLIENT_ID_PATTERN = re.compile(r"^amzn1\.application-oa2-client\.[0-9a-z]{32}$")
PRODUCT_ID_PATTERN = re.compile(r"^[0-9a-zA-Z_]+$")


def normalize_avs_config(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return wiki/genConfig.sh-compatible config with deviceInfo keys."""
    device = data.get("deviceInfo") if isinstance(data.get("deviceInfo"), dict) else data
    if not isinstance(device, dict):
        raise ValueError("config.json must be an object")

    client_id = device.get("clientId") or device.get("clientID")
    product_id = device.get("productId") or device.get("productID")
    if not client_id or not product_id:
        raise ValueError(
            "config.json must include deviceInfo.clientId and deviceInfo.productId"
        )
    if not PRODUCT_ID_PATTERN.fullmatch(str(product_id)):
        raise ValueError("productId must be alphanumeric/underscore (no spaces)")

    return {
        "deviceInfo": {
            "clientId": str(client_id),
            "productId": str(product_id),
        }
    }


def client_id_looks_valid(client_id: str) -> bool:
    return bool(CLIENT_ID_PATTERN.fullmatch(client_id))


def load_and_normalize_avs_config(path: Path) -> dict[str, dict[str, str]]:
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("config.json must contain a JSON object")
    return normalize_avs_config(data)
