#!/usr/bin/env python3
"""QRVault core logic."""
from __future__ import annotations

from .config import load_tool_data

import argparse
import csv
import ctypes
import ctypes.util
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote, urlparse

import qrcode
import qrcode.constants
import qrcode.image.svg
import requests
from PIL import Image
from rich.panel import Panel

from .utils import (
    console,
    make_table,
    print_error,
    print_info,
    print_success,
    print_tool_header,
    print_warning,
    prompt_confirm,
    prompt_menu,
    prompt_text,
    safe_filename,
    unique_path,
)

def _load_tool_data(filename: str) -> dict:
    """Thin alias: load this tool's own config via core/config.py."""
    return load_tool_data(filename)

URL_PATTERN = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)


@dataclass
class QRGenerationOptions:
    error_correction: str = "M"  # L | M | Q | H
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    back_color: str = "white"
    target_resolution: Optional[Tuple[int, int]] = None  # (width, height) in px for PNG
    export_format: str = "png"  # png | svg


@dataclass
class DecodedQRResult:
    image_path: Path
    symbol_type: str
    payload: str
    detected_urls: List[str] = field(default_factory=list)
    url_validations: Dict[str, Dict[str, Any]] = field(default_factory=dict)


TOOL_DATA = _load_tool_data("qr_defaults.json")
_ERROR_CORRECTION_CODE = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}
# Keep only levels still declared in the tool data file
ERROR_CORRECTION_MAP = {
    _lvl: _code
    for _lvl, _code in _ERROR_CORRECTION_CODE.items()
    if _lvl in TOOL_DATA.get("error_correction_levels", {})
}
DEFAULT_QR_FILL = TOOL_DATA.get("default_fill_color", "black")
DEFAULT_QR_BACK = TOOL_DATA.get("default_back_color", "white")
DEFAULT_QR_BOX_SIZE = int(TOOL_DATA.get("default_box_size", 10))
DEFAULT_QR_BORDER = int(TOOL_DATA.get("default_border", 4))
URL_CHECK_TIMEOUT = float(TOOL_DATA.get("url_check_timeout", 8.0))


def format_wifi_payload(
    ssid: str,
    password: str = "",
    security: str = "WPA",  # WPA | WEP | nopass
    hidden: bool = False,
) -> str:
    """Format a standard Wi-Fi connection QR payload string."""
    sec = security.upper() if security.lower() != "nopass" else "nopass"
    esc_ssid = ssid.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace(":", r"\:")
    esc_pass = password.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace(":", r"\:")
    hidden_str = "true" if hidden else "false"
    if sec == "nopass" or not password:
        return f"WIFI:T:nopass;S:{esc_ssid};H:{hidden_str};;"
    return f"WIFI:T:{sec};S:{esc_ssid};P:{esc_pass};H:{hidden_str};;"


def format_contact_vcard(
    full_name: str,
    phone: str = "",
    email: str = "",
    organization: str = "",
    title: str = "",
    url: str = "",
    address: str = "",
) -> str:
    """Format a vCard 3.0 contact QR payload."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{full_name}",
        f"N:{full_name};;;;",
    ]
    if organization:
        lines.append(f"ORG:{organization}")
    if title:
        lines.append(f"TITLE:{title}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{phone}")
    if email:
        lines.append(f"EMAIL:{email}")
    if url:
        lines.append(f"URL:{url}")
    if address:
        lines.append(f"ADR;TYPE=WORK:;;{address};;;;")
    lines.append("END:VCARD")
    return "\n".join(lines)


def format_email_payload(
    recipient: str,
    subject: str = "",
    body: str = "",
) -> str:
    """Format an email action mailto URI QR payload."""
    params: List[str] = []
    if subject:
        params.append(f"subject={quote(subject)}")
    if body:
        params.append(f"body={quote(body)}")
    query = f"?{'&'.join(params)}" if params else ""
    return f"mailto:{recipient}{query}"


def generate_qr_code(
    payload: str,
    output_path: Path | str,
    options: Optional[QRGenerationOptions] = None,
) -> Path:
    """Generate a QR code in PNG or SVG format with custom colors, resolution, and error correction."""
    opts = options or QRGenerationOptions()
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    ec_level = ERROR_CORRECTION_MAP.get(opts.error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
    fmt = (opts.export_format or out.suffix.lstrip(".") or "png").lower()

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=max(1, int(opts.box_size)),
        border=max(0, int(opts.border)),
    )
    qr.add_data(payload)
    qr.make(fit=True)

    if fmt == "svg" or out.suffix.lower() == ".svg":
        if out.suffix.lower() != ".svg":
            out = out.with_suffix(".svg")
        svg_img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        svg_bytes = svg_img.to_string()
        svg_text = svg_bytes.decode("utf-8") if isinstance(svg_bytes, bytes) else str(svg_bytes)
        # Apply custom foreground/background colors to SVG output
        if opts.fill_color and opts.fill_color.lower() != "black":
            svg_text = svg_text.replace('fill="#000000"', f'fill="{opts.fill_color}"')
        if opts.back_color and opts.back_color.lower() not in ("white", "transparent"):
            bg_rect = f'<rect width="100%" height="100%" fill="{opts.back_color}"/>'
            svg_text = re.sub(r"(<svg[^>]*>)", r"\1" + bg_rect, svg_text, count=1)
        out.write_text(svg_text, encoding="utf-8")
        return out

    # PNG / Raster generation
    if out.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        out = out.with_suffix(".png")
    pil_wrapper = qr.make_image(fill_color=opts.fill_color, back_color=opts.back_color)
    pil_img = pil_wrapper.get_image() if hasattr(pil_wrapper, "get_image") else pil_wrapper
    if not isinstance(pil_img, Image.Image):
        pil_img = pil_img.convert("RGB")
    else:
        pil_img = pil_img.convert("RGB")

    if opts.target_resolution:
        tw, th = opts.target_resolution
        if tw > 0 and th > 0:
            pil_img = pil_img.resize((int(tw), int(th)), Image.Resampling.NEAREST)

    pil_img.save(out)
    return out


def _decode_with_libzbar(image_path: Path) -> List[Tuple[str, str]]:
    """Decode QR/barcodes from a PIL-readable image using system libzbar via ctypes."""
    lib_name = ctypes.util.find_library("zbar")
    if not lib_name:
        raise RuntimeError("System library 'libzbar' not found for QR decoding.")

    lib = ctypes.cdll.LoadLibrary(lib_name)
    lib.zbar_image_scanner_create.restype = ctypes.c_void_p
    lib.zbar_image_scanner_destroy.argtypes = [ctypes.c_void_p]
    lib.zbar_image_scanner_set_config.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]
    lib.zbar_image_create.restype = ctypes.c_void_p
    lib.zbar_image_destroy.argtypes = [ctypes.c_void_p]
    lib.zbar_image_set_format.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    lib.zbar_image_set_size.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    lib.zbar_image_set_data.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_void_p,
    ]
    lib.zbar_scan_image.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.zbar_scan_image.restype = ctypes.c_int
    lib.zbar_image_first_symbol.argtypes = [ctypes.c_void_p]
    lib.zbar_image_first_symbol.restype = ctypes.c_void_p
    lib.zbar_symbol_next.argtypes = [ctypes.c_void_p]
    lib.zbar_symbol_next.restype = ctypes.c_void_p
    lib.zbar_symbol_get_data.argtypes = [ctypes.c_void_p]
    lib.zbar_symbol_get_data.restype = ctypes.c_char_p
    lib.zbar_symbol_get_type.argtypes = [ctypes.c_void_p]
    lib.zbar_symbol_get_type.restype = ctypes.c_int
    lib.zbar_get_symbol_name.argtypes = [ctypes.c_int]
    lib.zbar_get_symbol_name.restype = ctypes.c_char_p

    with Image.open(image_path) as img:
        gray = img.convert("L")
        width, height = gray.size
        raw_bytes = gray.tobytes()

    scanner = lib.zbar_image_scanner_create()
    zimg = lib.zbar_image_create()
    decoded_items: List[Tuple[str, str]] = []
    try:
        lib.zbar_image_scanner_set_config(scanner, 0, 0, 1)
        y800_fourcc = int.from_bytes(b"Y800", "little")
        lib.zbar_image_set_format(zimg, y800_fourcc)
        lib.zbar_image_set_size(zimg, width, height)
        lib.zbar_image_set_data(zimg, raw_bytes, len(raw_bytes), None)

        lib.zbar_scan_image(scanner, zimg)
        sym = lib.zbar_image_first_symbol(zimg)
        while sym:
            sym_type_id = lib.zbar_symbol_get_type(sym)
            sym_name_ptr = lib.zbar_get_symbol_name(sym_type_id)
            sym_name = sym_name_ptr.decode("utf-8", errors="replace") if sym_name_ptr else "QR-Code"
            data_ptr = lib.zbar_symbol_get_data(sym)
            payload = data_ptr.decode("utf-8", errors="replace") if data_ptr else ""
            decoded_items.append((sym_name, payload))
            sym = lib.zbar_symbol_next(sym)
    finally:
        lib.zbar_image_destroy(zimg)
        lib.zbar_image_scanner_destroy(scanner)

    return decoded_items


def validate_url_syntax(url: str) -> Tuple[bool, str]:
    """Validate whether a string is a syntactically well-formed HTTP/HTTPS URL."""
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return (False, "Scheme must be http or https")
        if not parsed.netloc or "." not in parsed.netloc and parsed.hostname != "localhost":
            return (False, "Missing valid domain/host")
        return (True, "Valid URL syntax")
    except Exception as exc:
        return (False, str(exc))


def check_url_accessibility(
    url: str,
    timeout: float = URL_CHECK_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """Validate URL syntax and optionally check live HTTP accessibility without opening a browser."""
    syntax_ok, syntax_msg = validate_url_syntax(url)
    info: Dict[str, Any] = {
        "url": url,
        "syntax_valid": syntax_ok,
        "syntax_message": syntax_msg,
        "accessible": None,
        "http_status": None,
        "final_url": None,
        "error": None,
    }
    if not syntax_ok:
        info["accessible"] = False
        return info

    sess = session or requests.Session()
    try:
        resp = sess.head(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": "QRVault/1.0"})
        if resp.status_code >= 400:
            resp = sess.get(url, allow_redirects=True, timeout=timeout, stream=True, headers={"User-Agent": "QRVault/1.0"})
            resp.close()
        info["http_status"] = resp.status_code
        info["final_url"] = resp.url
        info["accessible"] = 200 <= resp.status_code < 400
    except Exception as exc:
        info["accessible"] = False
        info["error"] = str(exc)
    return info


def decode_qr_image(
    image_path: Path | str,
    check_accessibility: bool = False,
    timeout: float = 8.0,
    session: Optional[requests.Session] = None,
) -> List[DecodedQRResult]:
    """Decode QR code(s) from an image file and validate any embedded URLs."""
    p = Path(image_path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"QR image file not found: {p}")

    raw_symbols = _decode_with_libzbar(p)
    results: List[DecodedQRResult] = []
    for sym_type, payload in raw_symbols:
        urls = URL_PATTERN.findall(payload)
        if not urls:
            syntax_ok, _ = validate_url_syntax(payload)
            if syntax_ok:
                urls = [payload.strip()]

        validations: Dict[str, Dict[str, Any]] = {}
        for u in urls:
            if check_accessibility:
                validations[u] = check_url_accessibility(u, timeout=timeout, session=session)
            else:
                ok, msg = validate_url_syntax(u)
                validations[u] = {
                    "url": u,
                    "syntax_valid": ok,
                    "syntax_message": msg,
                    "accessible": None,
                    "http_status": None,
                }

        results.append(
            DecodedQRResult(
                image_path=p,
                symbol_type=sym_type,
                payload=payload,
                detected_urls=urls,
                url_validations=validations,
            )
        )
    return results


def batch_generate_qr_codes(
    input_file: Path | str,
    output_dir: Path | str = "qrvault_batch",
    options: Optional[QRGenerationOptions] = None,
) -> List[Path]:
    """Generate multiple QR codes from a CSV, JSON, or TXT file."""
    in_path = Path(input_file).expanduser().resolve()
    out_root = Path(output_dir).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    opts = options or QRGenerationOptions()

    ext = in_path.suffix.lower()
    items: List[Tuple[str, str]] = []  # (name, payload)

    if ext == ".json":
        raw_data = json.loads(in_path.read_text(encoding="utf-8"))
        if isinstance(raw_data, list):
            for idx, entry in enumerate(raw_data, start=1):
                if isinstance(entry, str):
                    items.append((f"qr_{idx:03d}", entry))
                elif isinstance(entry, dict):
                    name = str(entry.get("name") or entry.get("id") or f"qr_{idx:03d}")
                    data = str(entry.get("data") or entry.get("payload") or entry.get("url") or entry.get("text") or "")
                    if data:
                        items.append((name, data))
    elif ext == ".csv":
        with open(in_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames and any(k.lower() in ("data", "payload", "url", "text") for k in reader.fieldnames):
                for idx, row in enumerate(reader, start=1):
                    row_low = {k.lower(): v for k, v in row.items() if k}
                    name = row_low.get("name") or row_low.get("filename") or f"qr_{idx:03d}"
                    data = row_low.get("data") or row_low.get("payload") or row_low.get("url") or row_low.get("text") or ""
                    if data:
                        items.append((str(name), str(data)))
            else:
                fh.seek(0)
                raw_reader = csv.reader(fh)
                for idx, r in enumerate(raw_reader, start=1):
                    if not r:
                        continue
                    if len(r) >= 2:
                        items.append((r[0].strip() or f"qr_{idx:03d}", r[1].strip()))
                    else:
                        items.append((f"qr_{idx:03d}", r[0].strip()))
    else:
        # Plain text: one QR payload per non-empty line
        for idx, line in enumerate(in_path.read_text(encoding="utf-8").splitlines(), start=1):
            clean = line.strip()
            if clean and not clean.startswith("#"):
                items.append((f"qr_{idx:03d}", clean))

    generated_files: List[Path] = []
    file_ext = ".svg" if opts.export_format.lower() == "svg" else ".png"
    for name, payload in items:
        dest = unique_path(out_root / f"{safe_filename(name)}{file_ext}")
        saved = generate_qr_code(payload, dest, options=opts)
        generated_files.append(saved)

    return generated_files


def display_decoded_results(results: Sequence[DecodedQRResult]) -> None:
    if not results:
        print_warning("No QR codes detected in the image.")
        return

    for idx, res in enumerate(results, start=1):
        console.print()
        console.print(
            Panel(
                res.payload,
                title=f"Decoded QR #{idx} Preview ({res.symbol_type}) - {res.image_path.name}",
                border_style="bright_cyan",
            )
        )
        if res.detected_urls:
            rows = []
            for u, v in res.url_validations.items():
                syn = "[green]Valid[/green]" if v.get("syntax_valid") else f"[red]Invalid ({v.get('syntax_message')})[/red]"
                acc = v.get("accessible")
                if acc is None:
                    acc_str = "[dim]Not checked (offline validation)[/dim]"
                elif acc:
                    acc_str = f"[green]Accessible (HTTP {v.get('http_status')})[/green]"
                else:
                    acc_str = f"[red]Unreachable ({v.get('error') or v.get('http_status')})[/red]"
                rows.append((u, syn, acc_str))
            console.print(
                make_table(
                    title="Embedded URL Validation",
                    columns=[
                        ("Detected URL", "bold cyan"),
                        ("Syntax Validation", "white"),
                        ("Accessibility Check", "white"),
                    ],
                    rows=rows,
                )
            )
