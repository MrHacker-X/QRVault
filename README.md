<div align="center">

# ⃤ Q R V A U L T ⃤

### *Generate, decode, and verify QR codes - one command.*

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![OS](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Stars](https://img.shields.io/github/stars/MrHacker-X/qrvault?style=flat-square&color=orange)
![Forks](https://img.shields.io/github/forks/MrHacker-X/qrvault?style=flat-square&color=cyan)

</div>

---

## 📋 Table of Contents

- [🎯 Why QRVault?](#-why-qrvault)
- [🧭 What It Does](#-what-it-does)
- [🚀 Quick Start](#-quick-start)
- [🖼️ Preview](#-preview)
- [📦 Installation](#-installation)
- [✨ Features](#-features)
- [⌨️ Usage](#%EF%B8%8F-usage)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🧰 Tech Stack](#-tech-stack)
- [⚠️ Disclaimer](#%EF%B8%8F-disclaimer)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [👨‍💻 Developer](#-developer)

---

## 🎯 Why QRVault?

> Making a QR code shouldn't mean pasting your data into a random web generator you can't audit. **QRVault does it entirely offline in two commands**: encode any text or URL into a QR image with your chosen error-correction level, and decode any QR image back to text - including validating whether what it contains is a safe link.
>
> **Your data never leaves your machine.** Generation and decoding are pure local processing - no web services involved at any step.

---

## 🧭 What It Does

| # | Task | What it gives you |
|---|------|-------------------|
| 1️⃣ | Generate QR payloads | Plain text, URLs, Wi-Fi joins, contacts (vCard), and email/SMS - into PNG or SVG |
| 2️⃣ | Style the output | Custom foreground/background colors, size, box size, and border spacing |
| 3️⃣ | Decode an image | Extract the text payload back from any QR image, optionally with `--check-url` validation |
| 4️⃣ | Batch mode | Encode a whole CSV/JSON/TXT list of payloads in one run |

---

## 🚀 Quick Start

```bash
git clone https://github.com/MrHacker-X/qrvault.git
cd qrvault
pip install -r requirements.txt
python qrvault.py                 # interactive menu
```

---

## 🖼️ Preview

<div align="center">

![QRVault Preview](https://i.ibb.co/m5bgjLJw/qrvault.png)

</div>

---

## 📦 Installation

```bash
# 1. clone
git clone https://github.com/MrHacker-X/qrvault.git
cd qrvault

# 2. install dependencies
pip install -r requirements.txt

# 3. run
python qrvault.py
```

### Supported Systems

| OS | Status | Notes |
|----|--------|-------|
| 🐧 Linux | ✅ Fully supported | Any distro with Python 3.8+ |
| 🪟 Windows | ✅ Fully supported | Python from python.org, then the steps above |
| 🍎 macOS | ✅ Fully supported | `brew install python`, then the steps above |
| 📱 Termux (Android) | ✅ Fully supported | `pkg install python`, then the steps above |

> 💡 Everything is offline - QRVault talks to no web service when generating or decoding.

---

## ✨ Features

| | Feature | Description |
|---|---------|-------------|
| 🧬 | **Full ECC control** | L / M / Q / H error-correction levels, so damaged codes still decode |
| 🖼️ | **PNG output** | Crisp, scalable QR images written locally - no watermarks, no upload |
| 🖥️ | **Terminal preview** | Render a QR straight into the terminal for quick sharing without opening an image viewer |
| ✂️ | **Reliable decoding** | Reads QR payloads back from images via `pyzbar`, including camera-shot photos |
| 🛡️ | **URL validation** | Decoded payloads classified and checked (scheme + host) so you can trust - or distrust - what you scan |
| 🎛️ | **Two modes** | A guided interactive menu or a fully flag-driven direct CLI |
| 🧱 | **Fail-fast validation** | Bad images or payloads too long for a QR produce one clear message |
| 🪶 | **Minimal dependencies** | `qrcode`, `pyzbar`, `Pillow`, `rich`, nothing else |

---

## ⌨️ Usage

```bash
python qrvault.py                 # interactive menu
python qrvault.py -h              # help
python qrvault.py -v              # version
```

### Direct CLI

```bash
# generate a QR for a URL, saved to a PNG
python qrvault.py -a url -d "https://example.com" -o qr.png

# generate a Wi-Fi join QR with high error correction
python qrvault.py -a wifi --ssid MyNet --password secret --security WPA -e H --size 512

# decode a QR image back to text (and vote on the URL)
python qrvault.py -a decode -d qr.png --check-url
```

| Option | Values / Example | Meaning |
|--------|------------------|---------|
| `-a` / `--action` | `text` / `url` / `wifi` / `contact` / `email` / `decode` / `batch` | QR type to make (default `text`) |
| `-d` / `--data` | text, URL, or image path | Payload to encode, or image to decode |
| `-o` / `--output` | a filename (default `qrcode.png`) | Where the PNG/SVG lands |
| `-e` / `--ecc` | `L` / `M` / `Q` / `H` | Error-correction level |
| `--fg` / `--bg` | color names or hex codes | QR and background colors |
| `--size` / `--box-size` / `--border` | numbers | Output resolution, module size, and quiet zone |
| `--check-url` | flag | Validate a decoded URL for scheme + host |

---

## ⚙️ Configuration

Behavior lives in [`core/config.py`](core/config.py):

| Setting | Default | Effect |
|---------|---------|--------|
| ECC map | `L/M/Q/H` → error-correction % | How each level maps to redundancy |
| Default ECC | `M` | Level used when none is passed |
| Default fill/border | sensible margins | Size and quiet zone of generated codes |
| URL verdict rules | scheme + host checks | What counts as a "valid" URL in a decoded payload |

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ |
| Generation | `qrcode` (with `Pillow` for image output) |
| Decoding | `pyzbar` (ZBar QR/barcode reader) |
| UI | `rich` (menus, colored tables, prompts) |

---

## ⚠️ Disclaimer

> ### Read this before using QRVault.
>
> 1. **Scan cautiously.** A decoded URL is not a safe URL - malicious QR codes are a real phishing vector. Always read `decode`'s validation verdict before opening anything.
> 2. **Don't encode secrets you'd regret.** QR codes are *not* encryption - anything you encode is readable by anyone who photographs the code. Never put passwords or keys into a QR you'll post publicly.
> 3. **pyzbar needs its native lib.** The decoder depends on the ZBar shared library (`libzbar0` on Debian/Ubuntu, `brew install zbar` on macOS). It won't silently misdecode - it fails with a clear message if absent.
> 4. **No warranty.** QRVault is provided "as is", with no warranty of any kind. The author is **not liable** for misuse, phishing losses, or damage from using this tool.

---

## 🤝 Contributing

Contributions are welcome!

```bash
# 1. fork it
# 2. create your branch
git checkout -b feature/amazing-feature
# 3. commit
git commit -m "Add amazing feature"
# 4. push
git push origin feature/amazing-feature
# 5. open a Pull Request
```

---

## 📜 License

QRVault is the original project by MrHacker-X - see the [`LICENSE`](https://github.com/MrHacker-X/qrvault) file in the upstream repository for details.

---

## 👨‍💻 Developer

| | |
|---|---|
| **Dev** | MrHacker-X |
| **GitHub** | [github.com/MrHacker-X](https://github.com/MrHacker-X) |
| **Email** | [contact@vritrasec.com](mailto:contact@vritrasec.com) |
| **Website** | [vritrasec.com](https://vritrasec.com) |
| **Network** | [link.vritrasec.com](https://link.vritrasec.com) |

---

<div align="center">

### ⭐ Star the repo if QRVault kept your codes offline ⭐

*Built by MrHacker-X - generate locally, decode cautiously.*

</div>
