<div align="center">
  <p>
    <a href="README_RU.md">🇷🇺 Русский</a> &nbsp;&nbsp;•&nbsp;&nbsp;
    <a href="README.md"><b>🇺🇸 English</b></a> &nbsp;&nbsp;•&nbsp;&nbsp;
    <a href="README_CN.md">🇨🇳 中文</a>
  </p>

  <h1>🛡️ ZeroExif</h1>
  <p><b>Advanced Terminal Utility for Complete Image Metadata Removal</b></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey" alt="Supported Platforms">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  </p>
</div>

<br>

ZeroExif is a powerful console-based script designed to strip EXIF, XMP, ICC, and other metadata from your images. It protects your privacy by removing GPS coordinates, camera models, and timestamps before you share your photos online.

Built with a custom rendering engine, it offers a seamless experience directly in your terminal, complete with Drag & Drop support and multilingual interfaces.

---

## 📥 Which version should I download?

The repository contains two versions of the script to ensure maximum compatibility across all environments. Choose the one that fits your setup:

| File | Best For | Description |
| :--- | :--- | :--- |
| **`ZeroExif.py`** | **Windows, macOS, Linux** | Features a rich interactive floating menu for settings. Best for desktop environments with full terminal capabilities. |
| **`ZeroExif_NO_TUI.py`** | **Termux (Android)** | A streamlined version without complex floating menus. <br>⚠️ **Crucial for Termux:** The interactive menus in the main version do not render correctly in Android's Termux, causing users to lose access to settings. Always use this version on mobile. |

---

## 🚀 Installation

Ensure you have Python installed on your system. 

**1. Clone the repository:**
```bash
git clone https://github.com/Datvex/ZeroExif.git
cd ZeroExif
```

**2. Install required dependencies:**
The script requires the `Pillow` library to process images.
```bash
pip install -r Requirements.txt
```

**3. Run the script:**
```bash
python ZeroExif.py
```

**3.1 Run the script (For Termux):**
```bash
python ZeroExif_NO_TUI.py
```

---

## 🕹️ Controls & Navigation

ZeroExif is designed to be fully controlled via your keyboard. 

### Main Menu
Use number keys to navigate.
* <kbd>1</kbd> **Start cleaning:** Move to the file selection step.
* <kbd>2</kbd> **Settings:** Change output directory or interface language (English, Русский, 中文).
* <kbd>Esc</kbd> **Exit:** Close the application securely.

### File Selection Phase
Instead of typing paths manually, you can simply **Drag & Drop** a folder or individual image files directly into the terminal window.

| Action | Key / Input |
| :--- | :--- |
| **Toggle file selection** | <kbd>1</kbd> – <kbd>10</kbd> (Type the number next to the file) |
| **Next Page** | <kbd>N</kbd> |
| **Previous Page** | <kbd>P</kbd> |
| **Add more files** | Drag & Drop more folders/files into the terminal |
| **Proceed to cleaning** | <kbd>0</kbd> |
| **Go back** | <kbd>Esc</kbd> |

### Metadata Selection Phase
Customize exactly what data you want to remove. Toggle options by pressing their corresponding numbers:

1. **All Metadata** (Recommended) - Removes EXIF, XMP, ICC.
2. **GPS / Location** - Strips only location coordinates.
3. **Camera & Lens Info** - Removes device specific data.
4. **Date & Time** - Deletes timestamps.

Press <kbd>0</kbd> to execute the cleaning process.

---

## 🛠️ Troubleshooting

> **Error: "Pillow library is not installed"**
> Run `pip install Pillow`. If you are on Linux, you might need `pip3 install Pillow`.

> **Cannot open Settings in Termux / Interface freezes**
> You are running `ZeroExif.py` which contains desktop-specific UI rendering. Please switch to `ZeroExif_NO_TUI.py` for full functionality in Termux.

> **PermissionError / Access denied**
> Ensure the script has write permissions for your specified Output Path. If you are on Termux, ensure you have granted storage permissions via `termux-setup-storage`.
