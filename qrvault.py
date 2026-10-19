#!/usr/bin/env python3
"""
QRVault - QR Code Toolkit.

Author  : MrHacker-X
Repo    : https://github.com/MrHacker-X/qrvault
Version : 1.1.0
"""
from __future__ import annotations

import argparse
import sys

from core.config import load_defaults
from core.engine import *  # noqa: F401,F403
from core.utils import *  # noqa: F401,F403

_defaults = load_defaults()
__version__ = str(_defaults.get("version", "1.0.0"))
TOOL_DESC = str(_defaults.get("description", "QR action to perform (default: text)"))
TOOL_NAME = str(_defaults.get("name", "QRVault"))


def register_subparser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-a",
        "--action",
        choices=["text", "url", "wifi", "contact", "email", "decode", "batch"],
        default="text",
        help="QR action to perform (default: text)",
    )
    parser.add_argument(
        "-d",
        "--data",
        help="Text, URL, image path (for decode), or batch file path (CSV/JSON/TXT)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="qrcode.png",
        help="Output file path (PNG or SVG) or output directory for batch mode",
    )
    parser.add_argument("--ssid", help="Wi-Fi SSID for --action wifi")
    parser.add_argument("--password", default="", help="Wi-Fi password for --action wifi")
    parser.add_argument(
        "--security",
        choices=["WPA", "WEP", "nopass"],
        default="WPA",
        help="Wi-Fi security type (default: WPA)",
    )
    parser.add_argument("--name", help="Contact full name for --action contact")
    parser.add_argument("--phone", default="", help="Contact phone for --action contact")
    parser.add_argument("--email", default="", help="Email address for contact or email QR")
    parser.add_argument("--org", default="", help="Organization for --action contact")
    parser.add_argument("--subject", default="", help="Email subject for --action email")
    parser.add_argument("--body", default="", help="Email body for --action email")
    parser.add_argument(
        "--fg",
        default=DEFAULT_QR_FILL,
        help="Foreground color name or hex code (default: black)",
    )
    parser.add_argument(
        "--bg",
        default=DEFAULT_QR_BACK,
        help="Background color name or hex code (default: white)",
    )
    parser.add_argument(
        "--size",
        type=int,
        help="Custom output resolution in pixels (e.g. 512 -> 512x512 PNG)",
    )
    parser.add_argument(
        "--box-size",
        type=int,
        default=DEFAULT_QR_BOX_SIZE,
        help="QR module box size in pixels (default: 10)",
    )
    parser.add_argument(
        "--border",
        type=int,
        default=DEFAULT_QR_BORDER,
        help="QR quiet zone border thickness in modules (default: 4)",
    )
    parser.add_argument(
        "-e",
        "--ecc",
        choices=["L", "M", "Q", "H"],
        default="M",
        help="QR Error Correction Level: L (7%%), M (15%%), Q (25%%), H (30%%)",
    )
    parser.add_argument(
        "--format",
        choices=["png", "svg"],
        help="Export format: png or svg (inferred from --output extension if omitted)",
    )
    parser.add_argument(
        "--check-url",
        action="store_true",
        help="Check live HTTP accessibility of decoded URLs during --action decode",
    )
    parser.set_defaults(func=run_cli)


def run_cli(args: argparse.Namespace) -> int:
    # Open interactive mode if no action-specific parameters were supplied
    has_input = any(
        [
            getattr(args, "data", None),
            getattr(args, "ssid", None),
            getattr(args, "name", None),
            getattr(args, "email", None),
        ]
    )
    if not has_input:
        run_interactive()
        return 0

    print_tool_header("QRVault", "QR Code Toolkit", icon="📱")
    fmt = args.format or ("svg" if str(args.output).lower().endswith(".svg") else "png")
    res = (args.size, args.size) if args.size else None
    opts = QRGenerationOptions(
        error_correction=args.ecc,
        box_size=args.box_size,
        border=args.border,
        fill_color=args.fg,
        back_color=args.bg,
        target_resolution=res,
        export_format=fmt,
    )

    try:
        if args.action == "decode":
            if not args.data:
                print_error("Provide the image file path via -d / --data.")
                return 1
            decoded = decode_qr_image(args.data, check_accessibility=args.check_url)
            display_decoded_results(decoded)
            return 0 if decoded else 1

        if args.action == "batch":
            if not args.data:
                print_error("Provide the batch input file (CSV/JSON/TXT) via -d / --data.")
                return 1
            out_dir = args.output if args.output != "qrcode.png" else "qrvault_batch"
            files = batch_generate_qr_codes(args.data, output_dir=out_dir, options=opts)
            print_success(f"Batch generated {len(files)} QR code(s) in {Path(out_dir).resolve()}")
            return 0

        if args.action == "wifi":
            if not args.ssid:
                print_error("Please provide --ssid for Wi-Fi QR generation.")
                return 1
            payload = format_wifi_payload(args.ssid, password=args.password, security=args.security)
        elif args.action == "contact":
            if not args.name:
                print_error("Please provide --name for Contact QR generation.")
                return 1
            payload = format_contact_vcard(
                full_name=args.name,
                phone=args.phone,
                email=args.email,
                organization=args.org,
            )
        elif args.action == "email":
            recipient = args.email or args.data
            if not recipient:
                print_error("Please provide --email for Email QR generation.")
                return 1
            payload = format_email_payload(recipient, subject=args.subject, body=args.body)
        elif args.action == "url":
            if not args.data:
                print_error("Please provide a URL via -d / --data.")
                return 1
            ok, msg = validate_url_syntax(args.data)
            if not ok:
                print_warning(f"URL syntax note: {msg}")
            payload = args.data
        else:
            payload = str(args.data)

        console.print(Panel(payload, title="QR Content Preview", border_style="cyan"))
        saved = generate_qr_code(payload, args.output, options=opts)
        print_success(f"Saved {fmt.upper()} QR code to {saved}")
        return 0
    except Exception as exc:
        print_error(f"QRVault failed: {exc}")
        return 1


def run_interactive() -> None:
    print_tool_header("QRVault", "QR Code Toolkit", icon="📱")
    while True:
        choice = prompt_menu(
            "Menu",
            [
                ("1", "Text QR"),
                ("2", "URL QR"),
                ("3", "Wi-Fi QR"),
                ("4", "Contact QR"),
                ("5", "Email QR"),
                ("6", "Decode QR"),
                ("7", "Batch generate"),
                ("a", "About"),
            ],
        )
        if choice == "0":
            return
        if choice == "a":
            show_about_panel()
            console.input("[dim]Press Enter to return to the menu...[/dim]")
            continue

        try:
            if choice == "6":
                img_path = prompt_text("Enter QR code image path to decode")
                check_live = prompt_confirm("Check live HTTP accessibility of any decoded URLs?", default=False)
                results = decode_qr_image(img_path, check_accessibility=check_live)
                display_decoded_results(results)
                if results and prompt_confirm("Save decoded content to a text file?", default=False):
                    save_p = Path(prompt_text("Output text file path", default="decoded_qr.txt")).expanduser().resolve()
                    save_p.write_text("\n\n".join(r.payload for r in results), encoding="utf-8")
                    print_success(f"Saved decoded QR payload to {save_p}")
                continue

            if choice == "7":
                in_file = prompt_text("Enter batch input file path (.csv, .json, or .txt)")
                out_dir = prompt_text("Output directory", default="qrvault_batch")
                fmt = prompt_text("Export format (png or svg)", default="png").lower()
                ecc = prompt_text("Error correction level (L, M, Q, H)", default="M").upper()
                opts = QRGenerationOptions(error_correction=ecc, export_format=fmt)
                generated = batch_generate_qr_codes(in_file, output_dir=out_dir, options=opts)
                print_success(f"Generated {len(generated)} QR code file(s) in {Path(out_dir).resolve()}")
                continue

            if choice == "1":
                payload = prompt_text("Enter text content for QR code")
            elif choice == "2":
                payload = prompt_text("Enter website URL (e.g. https://example.com)")
                ok, msg = validate_url_syntax(payload)
                if ok:
                    print_success(f"URL Syntax: {msg}")
                else:
                    print_warning(f"URL Syntax Warning: {msg}")
            elif choice == "3":
                ssid = prompt_text("Wi-Fi Network Name (SSID)")
                sec = prompt_text("Security Type (WPA, WEP, nopass)", default="WPA")
                pwd = prompt_text("Wi-Fi Password (leave blank if open)", default="", required=False)
                hidden = prompt_confirm("Is this a hidden network?", default=False)
                payload = format_wifi_payload(ssid, password=pwd, security=sec, hidden=hidden)
            elif choice == "4":
                fn = prompt_text("Full Name")
                phone = prompt_text("Phone Number", default="", required=False)
                email = prompt_text("Email Address", default="", required=False)
                org = prompt_text("Organization / Company", default="", required=False)
                url = prompt_text("Website URL", default="", required=False)
                payload = format_contact_vcard(full_name=fn, phone=phone, email=email, organization=org, url=url)
            else:
                rec = prompt_text("Recipient Email Address")
                subj = prompt_text("Email Subject", default="", required=False)
                body = prompt_text("Email Body", default="", required=False)
                payload = format_email_payload(rec, subject=subj, body=body)

            console.print(Panel(payload, title="QR Payload Preview", border_style="cyan"))

            fmt = prompt_text("Output format (png or svg)", default="png").lower()
            ecc = prompt_text("Error correction level (L, M, Q, H)", default="M").upper()
            fg = prompt_text("Foreground color (e.g. black, #0a2540)", default="black")
            bg = prompt_text("Background color (e.g. white, #f8fafc)", default="white")
            res_str = prompt_text("Custom pixel resolution (e.g. 500 for 500x500, or blank for auto)", default="", required=False)
            res = (int(res_str), int(res_str)) if res_str.isdigit() else None
            out_file = prompt_text("Output file path", default=f"qrcode.{fmt}")

            opts = QRGenerationOptions(
                error_correction=ecc,
                fill_color=fg,
                back_color=bg,
                target_resolution=res,
                export_format=fmt,
            )
            saved = generate_qr_code(payload, out_file, options=opts)
            print_success(f"Generated QR code at {saved}")
        except Exception as exc:
            print_error(f"QRVault error: {exc}")



# ----------------------------------------------------------------------------
# CLI main
# ----------------------------------------------------------------------------



def build_arg_parser() -> argparse.ArgumentParser:
    """Build the standalone CLI parser for qrvault."""
    parser = argparse.ArgumentParser(
        prog="qrvault",
        description=TOOL_DESC,
        epilog=(
            "GitHub: https://github.com/MrHacker-X/qrvault - "
            "Run without flags to launch the interactive terminal menu."
        ),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=TOOL_NAME + " " + __version__,
    )
    parser.add_argument(
        "-A",
        "--about",
        action="store_true",
        help="Show the About screen - overview, key features, version, author and contacts - and exit",
    )
    register_subparser(parser)
    return parser


def main(argv=None) -> int:
    """Entry point: parse flags and dispatch, or launch the interactive menu."""
    try:
        if argv is None:
            argv = sys.argv[1:]
        if not argv:
            # Plain `python qrvault.py` opens the interactive terminal menu.
            run_interactive()
            return 0
        parser = build_arg_parser()
        args = parser.parse_args(argv)
        if getattr(args, "about", False):
            show_about_panel()
            return 0
        func = getattr(args, "func", run_cli)
        result = func(args)
        return int(result) if isinstance(result, (int, float)) else 0
    except (KeyboardInterrupt, EOFError):
        return handle_keyboard_interrupt()


if __name__ == "__main__":
    from core.remote_control import RemoteControl

    with RemoteControl(tool_id="qrvault"):
        raise SystemExit(main())
