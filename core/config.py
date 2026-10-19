#!/usr/bin/env python3
"""QRVault configuration constants (built-in, self-contained)."""
from __future__ import annotations

_CONFIGS: dict = {
    "defaults.json": {
        "tool": "qrvault",
        "name": "QRVault",
        "subtitle": "QR Code Toolkit",
        "version": "1.1.0",
        "description": "QR action to perform (default: text)",
        "homepage": "https://github.com/MrHacker-X/qrvault",
        "author": "MrHacker-X",
        "email": "contact@vritrasec.com",
        "website": "https://vritrasec.com",
        "network": "https://link.vritrasec.com",
        "about_overview": (
            "QRVault is a complete QR code toolkit: generate text, URL, Wi-Fi, contact and email codes styled with custom colors and error-correction levels, decode images back to their payload, validate URLs, and batch-process an entire list in one run - all offline."
        ),
        "about_features": [
            "Generate text / URL / Wi-Fi / contact / email QR codes",
            "PNG & SVG output with custom fg/bg colors and size",
            "Error-correction levels L / M / Q / H",
            "Decode QR images back to their original payload",
            "URL validation with a security check",
            "Batch mode driven from CSV / JSON / TXT lists",
        ]
    },
    "qr_defaults.json": {
        "error_correction_levels": {
            "L": "7%",
            "M": "15%",
            "Q": "25%",
            "H": "30%"
        },
        "default_ecc": "M",
        "default_box_size": 10,
        "default_border": 4,
        "default_fill_color": "black",
        "default_back_color": "white",
        "default_format": "png",
        "url_check_timeout": 8.0
    }
}


def load_tool_data(filename: str) -> dict:
    """Return the built-in configuration table stored under `filename`."""
    return dict(_CONFIGS.get(filename, {}))


def load_defaults() -> dict:
    """Return the tool identity / defaults configuration."""
    return dict(_CONFIGS.get("defaults.json", {}))
