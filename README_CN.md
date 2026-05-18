<div align="center">
  <p>
    <a href="README_RU.md">🇷🇺 Русский</a> &nbsp;&nbsp;•&nbsp;&nbsp;
    <a href="README.md">🇺🇸 English</a> &nbsp;&nbsp;•&nbsp;&nbsp;
    <a href="README_CN.md"><b>🇨🇳 中文</b></a>
  </p>

  <h1>🛡️ ZeroExif</h1>
  <p><b>高级终端工具，用于彻底清除图像元数据</b></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/支持平台-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey" alt="Supported Platforms">
    <img src="https://img.shields.io/badge/许可证-MIT-green.svg" alt="License">
  </p>
</div>

<br>

ZeroExif 是一款强大的基于控制台的跨平台脚本，旨在清除图像中的 EXIF、XMP、ICC 等隐藏数据。它可以删除 GPS 坐标、相机型号和拍摄时间，在您将照片分享到网络前保护您的隐私。

该脚本内置了自定义的终端界面渲染引擎，支持拖放 (Drag & Drop) 文件，并提供多语言界面。

---

## 📥 我应该下载哪个版本？

为了确保在所有设备上都能完美运行，代码库中提供了两个版本的脚本。请根据您的环境选择合适的版本：

| 文件 | 适用环境 | 描述 |
| :--- | :--- | :--- |
| **`ZeroExif.py`** | **Windows, macOS, Linux** | 包含丰富的交互式悬浮设置菜单。非常适合具有完整终端功能的桌面操作系统。 |
| **`ZeroExif_NO_TUI.py`** | **Termux (Android)** | 精简版本，没有复杂的悬浮元素。<br>⚠️ **Termux 用户必看：** 主版本中的交互式菜单无法在 Android 的 Termux 环境中正确渲染，会导致用户无法进入设置。在手机上请务必使用此版本！ |

---

## 🚀 安装指南

请确保您的系统已安装 Python。

**1. 克隆代码库：**
```bash
git clone https://github.com/Datvex/ZeroExif.git
cd ZeroExif
```

**2. 安装依赖：**
脚本需要使用 `Pillow` 库来处理图像。
```bash
pip install -r Requirements.txt
```

**3. 运行脚本：**
```bash
python ZeroExif.py
```

**3.1 运行脚本 (适用于 Termux)：**
```bash
python ZeroExif_NO_TUI.py
```

---

## 🕹️ 控制与导航

ZeroExif 完全针对键盘操作进行了优化。

### 主菜单
使用键盘上的数字键进行选择。
* <kbd>1</kbd> **开始清理：** 进入文件选择步骤。
* <kbd>2</kbd> **设置：** 更改输出目录或界面语言 (English, Русский, 中文)。
* <kbd>Esc</kbd> **退出：** 安全关闭程序。

### 文件选择阶段
您无需手动输入文件路径。只需将文件夹或单个图像文件直接 **拖放 (Drag & Drop)** 到终端窗口中即可。

| 操作 | 按键 / 输入 |
| :--- | :--- |
| **选中/取消选中文件** | <kbd>1</kbd> – <kbd>10</kbd> (输入文件旁边的数字) |
| **下一页** | <kbd>N</kbd> (Next) |
| **上一页** | <kbd>P</kbd> (Previous) |
| **添加更多照片** | 将更多文件夹/文件拖入终端 |
| **继续 (准备清理)** | <kbd>0</kbd> |
| **返回上一级** | <kbd>Esc</kbd> |

### 元数据选择阶段
您可以精确自定义要删除的数据。按相应的数字键来切换选项：

1. **所有元数据** (推荐) - 删除 EXIF、XMP、ICC。
2. **GPS / 坐标** - 仅清除位置信息。
3. **相机和镜头信息** - 删除设备型号和特定参数。
4. **日期和时间** - 删除照片创建的时间戳。

按 <kbd>0</kbd> 执行清理过程。

---

## 🛠️ 常见问题解答

> **错误：未安装 Pillow 库**
> 运行命令 `pip install Pillow`。如果您使用的是 Linux，可能需要使用 `pip3 install Pillow`。

> **在 Termux 中无法打开设置 / 界面卡死**
> 您正在运行包含 PC 专属图形界面的 `ZeroExif.py`。请切换到专为 Termux 适配的 `ZeroExif_NO_TUI.py`。

> **错误：拒绝访问 (PermissionError)**
> 请确保脚本对您指定的“输出路径”具有写入权限。如果您使用的是 Termux，请先通过 `termux-setup-storage` 命令授予存储访问权限。
