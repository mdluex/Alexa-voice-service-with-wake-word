from __future__ import annotations

import json
from pathlib import Path

import pytest

from pi_voice_assistant.avs_config import (
    client_id_looks_valid,
    load_and_normalize_avs_config,
    normalize_avs_config,
)


def test_normalize_nested_device_info() -> None:
    data = {
        "deviceInfo": {
            "clientId": "amzn1.application-oa2-client.0123456789abcdef0123456789abcdef",
            "productId": "PrototypePi",
        }
    }
    assert normalize_avs_config(data) == data


def test_normalize_flat_keys() -> None:
    data = {
        "clientId": "amzn1.application-oa2-client.0123456789abcdef0123456789abcdef",
        "productId": "PrototypePi",
    }
    out = normalize_avs_config(data)
    assert out["deviceInfo"]["productId"] == "PrototypePi"


def test_rejects_product_id_with_spaces() -> None:
    with pytest.raises(ValueError, match="productId"):
        normalize_avs_config({"clientId": "x", "productId": "bad id"})


def test_load_and_normalize_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"clientId": "amzn1.application-oa2-client." + ("a" * 32), "productId": "Pi"}),
        encoding="utf-8",
    )
    out = load_and_normalize_avs_config(path)
    assert "deviceInfo" in out
    assert client_id_looks_valid(out["deviceInfo"]["clientId"])
