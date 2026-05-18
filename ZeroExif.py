import os
import sys
import json
import textwrap
import shlex
import urllib.parse
import time
import atexit
import unicodedata
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("\n\033[38;2;248;246;117mОшибка: Библиотека Pillow не установлена.\033[0m")
    print("Установите её командой: \033[1mpip install Pillow\033[0m\n")
    sys.exit(1)

C_BLUE = "\033[38;2;0;175;255m"
C_YELLOW = "\033[38;2;248;246;117m"
C_GRAY = "\033[38;2;110;110;110m"
C_WHITE = "\033[38;2;210;210;210m"
C_DARK_GRAY = "\033[38;2;80;80;80m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"
C_BG_INPUT = "\033[48;2;45;45;45m"

COLOR_NORMAL = {
    "blue": "\033[38;2;0;175;255m",
    "yellow": "\033[38;2;248;246;117m",
    "gray": "\033[38;2;110;110;110m",
    "white": "\033[38;2;210;210;210m",
    "dark_gray": "\033[38;2;80;80;80m",
    "bold": "\033[1m",
    "bg_input": "\033[48;2;45;45;45m"
}

COLOR_DIM = {
    "blue": "\033[38;2;0;65;95m",
    "yellow": "\033[38;2;95;94;45m",
    "gray": "\033[38;2;42;42;42m",
    "white": "\033[38;2;78;78;78m",
    "dark_gray": "\033[38;2;28;28;28m",
    "bold": "",
    "bg_input": "\033[48;2;22;22;22m"
}

def set_color_mode(dimmed=False):
    global C_BLUE, C_YELLOW, C_GRAY, C_WHITE, C_DARK_GRAY, C_BOLD, C_BG_INPUT
    palette = COLOR_DIM if dimmed else COLOR_NORMAL
    C_BLUE = palette["blue"]
    C_YELLOW = palette["yellow"]
    C_GRAY = palette["gray"]
    C_WHITE = palette["white"]
    C_DARK_GRAY = palette["dark_gray"]
    C_BOLD = palette["bold"]
    C_BG_INPUT = palette["bg_input"]

old_mode_in = None
old_mode_out = None
win32_available = False
win_mouse_left_down = False
_input_queue = []

if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32

    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    ENABLE_WINDOW_INPUT = 0x0008
    ENABLE_MOUSE_INPUT = 0x0010
    ENABLE_QUICK_EDIT_MODE = 0x0040
    ENABLE_EXTENDED_FLAGS = 0x0080
    ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    KEY_EVENT = 0x0001
    MOUSE_EVENT = 0x0002
    MOUSE_MOVED = 0x0001
    DOUBLE_CLICK = 0x0002
    MOUSE_WHEELED = 0x0004
    MOUSE_HWHEELED = 0x0008
    FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001

    VK_BACK = 0x08
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_UP = 0x26
    VK_DOWN = 0x28
    VK_C = 0x43

    LEFT_CTRL_PRESSED = 0x0008
    RIGHT_CTRL_PRESSED = 0x0004

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("bKeyDown", wintypes.BOOL),
            ("wRepeatCount", wintypes.WORD),
            ("wVirtualKeyCode", wintypes.WORD),
            ("wVirtualScanCode", wintypes.WORD),
            ("uChar", wintypes.WCHAR),
            ("dwControlKeyState", wintypes.DWORD)
        ]

    class MOUSE_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("dwMousePosition", COORD),
            ("dwButtonState", wintypes.DWORD),
            ("dwControlKeyState", wintypes.DWORD),
            ("dwEventFlags", wintypes.DWORD)
        ]

    class EVENT_UNION(ctypes.Union):
        _fields_ = [("KeyEvent", KEY_EVENT_RECORD), ("MouseEvent", MOUSE_EVENT_RECORD)]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [("EventType", wintypes.WORD), ("Event", EVENT_UNION)]

    hStdIn = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    hStdOut = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(hStdIn, ctypes.byref(mode)):
        old_mode_in = mode.value
        new_mode = mode.value
        new_mode &= ~ENABLE_QUICK_EDIT_MODE
        new_mode &= ~ENABLE_VIRTUAL_TERMINAL_INPUT
        new_mode |= ENABLE_EXTENDED_FLAGS
        new_mode |= ENABLE_MOUSE_INPUT
        new_mode |= ENABLE_WINDOW_INPUT
        kernel32.SetConsoleMode(hStdIn, new_mode)
        win32_available = True

    mode_out = ctypes.c_uint32()
    if kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode_out)):
        old_mode_out = mode_out.value
        new_mode_out = mode_out.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(hStdOut, new_mode_out)

    kernel32.GetNumberOfConsoleInputEvents.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetNumberOfConsoleInputEvents.restype = wintypes.BOOL
    kernel32.ReadConsoleInputW.argtypes = [wintypes.HANDLE, ctypes.POINTER(INPUT_RECORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel32.ReadConsoleInputW.restype = wintypes.BOOL
    kernel32.FlushConsoleInputBuffer.argtypes = [wintypes.HANDLE]
    kernel32.FlushConsoleInputBuffer.restype = wintypes.BOOL

def restore_console():
    if sys.platform == 'win32' and old_mode_in is not None:
        kernel32.SetConsoleMode(hStdIn, old_mode_in)
        if old_mode_out is not None:
            kernel32.SetConsoleMode(hStdOut, old_mode_out)

atexit.register(restore_console)

MEMORY_FILE = Path.home() / ".zeroexif_memory.json"

T = {
    "en": {
        "commands": "Commands",
        "actions": "Actions",
        "start": "Start cleaning",
        "settings": "Settings",
        "system": "System",
        "output_path": "Output path",
        "language": "Language",
        "lang_name": "English",
        "tip_main": "Type number to select, or Ctrl+C to exit",
        "action": "Action:",
        "change_path": "Change output path",
        "change_lang": "Change language",
        "new_path": "New path:",
        "path_updated": "Path successfully updated.",
        "press_enter": "Press Enter to continue",
        "press_enter_return": "Press Enter to return",
        "lang_updated": "Language successfully updated.",
        "target_dir": "Target Directory",
        "input": "Input",
        "enter_path": "Enter path, or Drag & Drop folder/images here",
        "path": "Path:",
        "err_not_found": "Error: Path or file not found.",
        "err_permission": "Error: Access denied (PermissionError).",
        "err_empty": "No supported images found.",
        "select_files": "Select Images",
        "dir": "Directory",
        "files": "Images",
        "selected": "Selected:",
        "of": "of",
        "tip_toggle": "1-10 to toggle, 'n'/'p' for pages, 0 to next step, or Drag & Drop more",
        "toggle": "Toggle/Page:",
        "err_no_selected": "No images selected.",
        "success": "Success",
        "success_msg": "EXIF data successfully removed.",
        "output_loc": "Output location",
        "err_save": "Save error(s) occurred:",
        "exif_title": "Select data to remove",
        "exif_all": "All Metadata (EXIF, XMP, ICC) - Recommended",
        "exif_gps": "GPS / Location Coordinates",
        "exif_cam": "Camera & Lens Information",
        "exif_date": "Date & Time",
        "tip_exif": "Type 1-4 to toggle, '0' to start cleaning"
    },
    "ru": {
        "commands": "Команды",
        "actions": "Действия",
        "start": "Начать очистку",
        "settings": "Настройки",
        "system": "Система",
        "output_path": "Путь сохранения",
        "language": "Язык",
        "lang_name": "Русский",
        "tip_main": "Введите номер для выбора, или Ctrl+C для выхода",
        "action": "Действие:",
        "change_path": "Изменить путь сохранения",
        "change_lang": "Изменить язык",
        "new_path": "Новый путь:",
        "path_updated": "Путь успешно обновлен.",
        "press_enter": "Нажмите Enter для продолжения",
        "press_enter_return": "Нажмите Enter для возврата",
        "lang_updated": "Язык успешно обновлен.",
        "target_dir": "Целевая папка",
        "input": "Ввод",
        "enter_path": "Введите путь, либо перетащите папку/фото (Drag & Drop)",
        "path": "Путь:",
        "err_not_found": "Ошибка: Путь или файл не найден.",
        "err_permission": "Ошибка: Нет доступа к папке (PermissionError).",
        "err_empty": "Поддерживаемые изображения не найдены.",
        "select_files": "Выбор фото",
        "dir": "Директория",
        "files": "Фотографии",
        "selected": "Выбрано:",
        "of": "из",
        "tip_toggle": "1-10 для выбора, 'n'/'p' для страниц, 0 для продолжения, или перетащите еще",
        "toggle": "Выбор/Стр:",
        "err_no_selected": "Фотографии не выбраны.",
        "success": "Успешно",
        "success_msg": "Метаданные успешно удалены.",
        "output_loc": "Место сохранения",
        "err_save": "Возникли ошибки при сохранении:",
        "exif_title": "Выбор данных для удаления",
        "exif_all": "Все метаданные (EXIF, XMP, ICC) - Рекомендуется",
        "exif_gps": "GPS / Координаты съемки",
        "exif_cam": "Модель камеры и параметры объектива",
        "exif_date": "Дата и время съемки",
        "tip_exif": "Введите 1-4 для выбора, '0' для начала очистки"
    },
    "zh": {
        "commands": "命令",
        "actions": "操作",
        "start": "开始清理",
        "settings": "设置",
        "system": "系统",
        "output_path": "输出路径",
        "language": "语言",
        "lang_name": "中文",
        "tip_main": "输入数字进行选择，或按 Ctrl+C 退出",
        "action": "操作:",
        "change_path": "更改输出路径",
        "change_lang": "更改语言",
        "new_path": "新路径:",
        "path_updated": "路径已成功更新。",
        "press_enter": "按 Enter 键继续",
        "press_enter_return": "按 Enter 键返回",
        "lang_updated": "语言已成功更新。",
        "target_dir": "目标目录",
        "input": "输入",
        "enter_path": "输入路径，或将文件夹/照片拖放到此处 (Drag & Drop)",
        "path": "路径:",
        "err_not_found": "错误: 找不到路径或文件。",
        "err_permission": "错误: 拒绝访问 (PermissionError)。",
        "err_empty": "未找到支持的图像。",
        "select_files": "选择图像",
        "dir": "目录",
        "files": "照片",
        "selected": "已选择:",
        "of": "/",
        "tip_toggle": "1-10 切换, 'n'/'p' 翻页, 0 下一步, 或拖放更多照片",
        "toggle": "切换/翻页:",
        "err_no_selected": "未选择任何照片。",
        "success": "成功",
        "success_msg": "EXIF 数据已成功删除。",
        "output_loc": "输出位置",
        "err_save": "保存时发生错误:",
        "exif_title": "选择要删除的数据",
        "exif_all": "所有元数据 (推荐)",
        "exif_gps": "GPS / 位置坐标",
        "exif_cam": "相机和镜头信息",
        "exif_date": "日期和时间",
        "tip_exif": "输入 1-4 进行切换，'0' 开始清理"
    }
}

class RawInput:
    def __enter__(self):
        if sys.platform != 'win32':
            import tty, termios
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, *args):
        if sys.platform != 'win32':
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

def char_width(ch):
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1

def text_width(text):
    return sum(char_width(ch) for ch in str(text))

def truncate_text(text, max_len):
    text = str(text)
    if max_len <= 0:
        return ""
    if text_width(text) <= max_len:
        return text
    if max_len <= 3:
        return "." * max_len
    result = ""
    width = 0
    limit = max_len - 3
    for ch in text:
        cw = char_width(ch)
        if width + cw > limit:
            break
        result += ch
        width += cw
    return result + "..."

def pad_text(text, width):
    text = str(text)
    return text + " " * max(0, width - text_width(text))

def flush_input_events():
    global win_mouse_left_down, _input_queue
    win_mouse_left_down = False
    if sys.platform == 'win32' and win32_available:
        kernel32.FlushConsoleInputBuffer(hStdIn)
    elif sys.platform == 'win32':
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getwch()
        except Exception:
            pass
    else:
        _input_queue.clear()
        try:
            import select
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0)
                if not r:
                    break
                os.read(sys.stdin.fileno(), 4096)
        except Exception:
            pass

def parse_vt_sequence(seq):
    if seq == '\x1b[A':
        return 'UP'
    if seq == '\x1b[B':
        return 'DOWN'
    if seq.startswith('\x1b[<') and seq.endswith(('M', 'm')):
        parts = seq[3:-1].split(';')
        if len(parts) == 3:
            cb, cx, cy = parts
            try:
                cb = int(cb)
                cx = int(cx)
                cy = int(cy)
                final = seq[-1]
                if cb & 64:
                    return 'IGNORE'
                if final == 'M':
                    if cb & 32:
                        return ('HOVER', cx, cy)
                    if (cb & 3) == 0:
                        return ('CLICK', cx, cy)
                    return ('HOVER', cx, cy)
                return 'IGNORE'
            except ValueError:
                pass
    if seq.startswith('\x1b[M') and len(seq) >= 6:
        try:
            cb = ord(seq[3]) - 32
            cx = ord(seq[4]) - 32
            cy = ord(seq[5]) - 32
            if cb & 64:
                return 'IGNORE'
            if cb & 32:
                return ('HOVER', cx, cy)
            if (cb & 3) == 0:
                return ('CLICK', cx, cy)
            return ('HOVER', cx, cy)
        except Exception:
            pass
    return seq

def get_win32_event():
    global win_mouse_left_down
    count = wintypes.DWORD()
    if not kernel32.GetNumberOfConsoleInputEvents(hStdIn, ctypes.byref(count)):
        time.sleep(0.01)
        return None
    if count.value == 0:
        time.sleep(0.01)
        return None
    record = INPUT_RECORD()
    read = wintypes.DWORD()
    while count.value > 0:
        if not kernel32.ReadConsoleInputW(hStdIn, ctypes.byref(record), 1, ctypes.byref(read)):
            time.sleep(0.01)
            return None
        kernel32.GetNumberOfConsoleInputEvents(hStdIn, ctypes.byref(count))
        if record.EventType == KEY_EVENT:
            key = record.Event.KeyEvent
            if not key.bKeyDown:
                continue
            vk = key.wVirtualKeyCode
            ch = key.uChar
            ctrl = key.dwControlKeyState & (LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED)
            if ctrl and vk == VK_C:
                raise KeyboardInterrupt
            if vk == VK_ESCAPE:
                return 'ESC'
            if vk == VK_RETURN:
                return 'ENTER'
            if vk == VK_BACK:
                return 'BACKSPACE'
            if vk == VK_UP:
                return 'UP'
            if vk == VK_DOWN:
                return 'DOWN'
            if ch and ch not in ('\x00', '\r', '\n', '\b', '\x1b'):
                return ch
        elif record.EventType == MOUSE_EVENT:
            mouse = record.Event.MouseEvent
            x = int(mouse.dwMousePosition.X) + 1
            y = int(mouse.dwMousePosition.Y) + 1
            flags = mouse.dwEventFlags
            left_down = bool(mouse.dwButtonState & FROM_LEFT_1ST_BUTTON_PRESSED)
            if flags == MOUSE_MOVED:
                win_mouse_left_down = left_down
                return ('HOVER', x, y)
            if flags == 0:
                if left_down and not win_mouse_left_down:
                    win_mouse_left_down = True
                    return ('CLICK', x, y)
                if not left_down:
                    win_mouse_left_down = False
                    return 'IGNORE'
            if flags in (DOUBLE_CLICK, MOUSE_WHEELED, MOUSE_HWHEELED):
                return 'IGNORE'
    return None

def get_event():
    global _input_queue
    if sys.platform == 'win32' and win32_available:
        return get_win32_event()
    elif sys.platform == 'win32':
        import msvcrt
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == '\x1b':
                seq = "\x1b"
                time.sleep(0.01)
                while msvcrt.kbhit():
                    seq += msvcrt.getwch()
                if seq == '\x1b':
                    return 'ESC'
                return parse_vt_sequence(seq)
            elif ch in ('\r', '\n'):
                return 'ENTER'
            elif ch == '\b':
                return 'BACKSPACE'
            elif ch == '\x03':
                raise KeyboardInterrupt
            elif ch in ('\x00', '\xe0'):
                ch2 = msvcrt.getwch()
                if ch2 == 'H':
                    return 'UP'
                elif ch2 == 'P':
                    return 'DOWN'
            else:
                return ch
        time.sleep(0.01)
        return None
    else:
        import select
        if not _input_queue:
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            if r:
                try:
                    data = os.read(sys.stdin.fileno(), 4096).decode('utf-8', errors='replace')
                    _input_queue.extend(list(data))
                except Exception:
                    pass

        if not _input_queue:
            return None

        ch = _input_queue.pop(0)

        if ch == '\x1b':
            seq = '\x1b'
            if not _input_queue:
                r2, _, _ = select.select([sys.stdin], [], [], 0.02)
                if r2:
                    try:
                        data = os.read(sys.stdin.fileno(), 4096).decode('utf-8', errors='replace')
                        _input_queue.extend(list(data))
                    except Exception:
                        pass
            if _input_queue and _input_queue[0] in ('[', 'O'):
                seq += _input_queue.pop(0)
                while True:
                    if not _input_queue:
                        r3, _, _ = select.select([sys.stdin], [], [], 0.01)
                        if r3:
                            try:
                                data = os.read(sys.stdin.fileno(), 4096).decode('utf-8', errors='replace')
                                _input_queue.extend(list(data))
                            except Exception:
                                pass
                        else:
                            break
                    if _input_queue:
                        next_ch = _input_queue.pop(0)
                        seq += next_ch
                        if next_ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz~M':
                            break
                    else:
                        break
                return parse_vt_sequence(seq)
            else:
                return 'ESC'
        elif ch in ('\n', '\r'):
            return 'ENTER'
        elif ch in ('\x7f', '\b'):
            return 'BACKSPACE'
        elif ch == '\x03':
            raise KeyboardInterrupt
        elif ch == '\x04':
            raise EOFError
        else:
            return ch

def clean_path(p):
    if not p:
        return p
    p = p.strip(' "\'\r\n\t')
    if p.startswith("file://"):
        p = p[7:]
        p = urllib.parse.unquote(p)
        if sys.platform == 'win32' and p.startswith('/') and len(p) > 2 and p[2] == ':':
            p = p[1:]
    if sys.platform == 'win32' and p.startswith('/') and len(p) >= 2 and p[1].isalpha() and (len(p) == 2 or p[2] == '/'):
        p = p[1] + ":" + p[2:]
    p = os.path.expanduser(p)
    p = os.path.normpath(p)
    return p

def parse_dropped_paths(raw_input):
    c_path = clean_path(raw_input)
    if os.path.exists(c_path):
        return [c_path]
    try:
        tokens = shlex.split(raw_input, posix=(os.name == 'posix'))
    except ValueError:
        tokens = raw_input.split()

    valid = []
    for t in tokens:
        ct = clean_path(t)
        if os.path.exists(ct):
            valid.append(ct)
    return valid

def is_image_file(filepath):
    ext = str(filepath).lower().split('.')[-1]
    return ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_memory(target_dir, disabled_files):
    memory = load_memory()
    abs_dir = os.path.abspath(target_dir)
    memory[abs_dir] = {"disabled_files": disabled_files}
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=4)
    except IOError:
        pass

def get_default_download_path():
    if sys.platform == 'win32':
        return os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads')
    elif 'ANDROID_ROOT' in os.environ:
        return '/storage/emulated/0/Download'
    else:
        return os.path.join(str(Path.home()), 'Downloads')

def load_config():
    mem = load_memory()
    conf = mem.get("_config_", {})
    lang = conf.get("lang", "en")
    out = conf.get("out", get_default_download_path())
    return lang, clean_path(out)

def save_config(lang, out):
    mem = load_memory()
    mem["_config_"] = {"lang": lang, "out": out}
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(mem, f, ensure_ascii=False, indent=4)
    except IOError:
        pass

def get_term_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

def get_layout():
    tw = get_term_width()
    bw = max(10, min(tw - 4, 70))
    m_len = max(0, (tw - bw) // 2)
    return tw, bw, " " * m_len

def clear_screen(lines=18):
    sys.stdout.write(f"{C_RESET}\033[2J\033[H")
    try:
        th = os.get_terminal_size().lines
        v_pad = max(0, (th - lines) // 2)
        if v_pad > 0:
            sys.stdout.write("\n" * v_pad)
    except OSError:
        pass
    sys.stdout.flush()

def draw_logo():
    ASCII_LOGO = [
        "▄▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄   ▄▄▄    ▄▄▄▄▄ ▄▄ ▄▄ ▄▄ ▄▄▄▄▄",
        "  ▄█▀ ██▄▄  ██▄█▄ ██▀██   ██▄▄  ▀█▄█▀ ██ ██▄▄ ",
        "▄██▄▄ ██▄▄▄ ██ ██ ▀███▀   ██▄▄▄ ██ ██ ██ ██   ",
        "~~~~~ ~~~~~ ~~ ~~  ~~~    ~~~~~ ~~ ~~ ~~ ~~   "
    ]
    C_SHADOW_FG = "\033[38;2;90;90;40m"
    if C_YELLOW == COLOR_DIM["yellow"]:
        C_SHADOW_FG = "\033[38;2;34;34;16m"
        
    tw = get_term_width()
    logo_width = len(ASCII_LOGO[0])
    indent = " " * max(0, (tw - logo_width) // 2)
    print()
    for line in ASCII_LOGO:
        rendered_line = indent
        for char in line:
            if char == ' ':
                rendered_line += " "
            elif char == '~':
                rendered_line += f"{C_SHADOW_FG}▀{C_RESET}"
            else:
                rendered_line += f"{C_YELLOW}{char}{C_RESET}"
        print(rendered_line)
    print("\n")

def print_tip(text, m, bw):
    lines = textwrap.wrap(text, width=max(10, bw - 6))
    if lines:
        print(f"\n{m}{C_YELLOW}● Tip{C_RESET} {C_GRAY}{lines[0]}{C_RESET}")
        for line in lines[1:]:
            print(f"{m}      {C_GRAY}{line}{C_RESET}")
    print()

def show_floating_modal(title, items, bg_draw_func):
    flush_input_events()
    max_len = text_width(title) + 10
    for item in items:
        l = text_width(item["label"]) + (text_width(item.get("shortcut", "")) + 4 if item.get("shortcut") else 0)
        if l > max_len:
            max_len = l
    mw = min(80, max(40, max_len + 6))
    mh = len(items) + 4
    sys.stdout.write("\033[?1000h\033[?1002h\033[?1003h\033[?1015h\033[?1006h\033[?25l")
    sys.stdout.flush()
    try:
        selectable = [i for i, it in enumerate(items) if it["type"] == "item"]
        if not selectable:
            return None
        sel_pos = 0
        last_size = (-1, -1)
        force_redraw = True
        sx = 1
        sy = 1

        def draw_dimmed_background():
            try:
                set_color_mode(True)
                bg_draw_func()
            finally:
                set_color_mode(False)

        def update_hover_selection(my):
            nonlocal sel_pos, force_redraw
            best_dist = 99999
            best_idx = sel_pos
            for i_sel, row_idx in enumerate(selectable):
                item_y = sy + 2 + row_idx
                dist = abs(my - item_y)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i_sel
            if best_idx != sel_pos:
                sel_pos = best_idx
                force_redraw = True

        with RawInput():
            while True:
                tw = get_term_width()
                try:
                    th = os.get_terminal_size().lines
                except OSError:
                    th = 24
                if (tw, th) != last_size:
                    draw_dimmed_background()
                    last_size = (tw, th)
                    force_redraw = True
                if force_redraw:
                    sx = max(1, (tw - mw) // 2)
                    sy = max(1, (th - mh) // 2)
                    title_part = f"  {title}"
                    esc_part = "esc  "
                    title_spaces = " " * max(0, mw - text_width(title_part) - text_width(esc_part))
                    sys.stdout.write(f"\033[{sy};{sx}H")
                    sys.stdout.write(f"\033[48;2;30;30;30m\033[38;2;210;210;210m{title_part}{title_spaces}\033[38;2;110;110;110m{esc_part}\033[0m")
                    sys.stdout.write(f"\033[{sy+1};{sx}H\033[48;2;30;30;30m{' ' * mw}\033[0m")
                    for i, item in enumerate(items):
                        sys.stdout.write(f"\033[{sy+2+i};{sx}H")
                        is_sel = selectable[sel_pos] == i
                        if item["type"] == "category":
                            line = pad_text(f"  {item['label']}", mw)
                            sys.stdout.write(f"\033[48;2;30;30;30m\033[38;2;0;175;255m{line}\033[0m")
                        else:
                            bg = "\033[48;2;248;246;117m" if is_sel else "\033[48;2;30;30;30m"
                            fg = "\033[38;2;0;0;0m" if is_sel else "\033[38;2;210;210;210m"
                            s_fg = "\033[38;2;80;80;80m" if is_sel else "\033[38;2;110;110;110m"
                            lbl = item["label"]
                            sh = item.get("shortcut", "")
                            sp = max(0, mw - text_width(lbl) - text_width(sh) - 4)
                            sys.stdout.write(f"{bg}{fg}  {lbl}{' ' * sp}{s_fg}{sh}  \033[0m")
                    sys.stdout.write(f"\033[{sy+2+len(items)};{sx}H\033[48;2;30;30;30m{' ' * mw}\033[0m")
                    sys.stdout.write(f"\033[{sy+3+len(items)};{sx}H\033[48;2;30;30;30m{' ' * mw}\033[0m")
                    sys.stdout.flush()
                    force_redraw = False
                ev = get_event()
                if ev:
                    if ev == 'UP':
                        sel_pos = (sel_pos - 1) % len(selectable)
                        force_redraw = True
                    elif ev == 'DOWN':
                        sel_pos = (sel_pos + 1) % len(selectable)
                        force_redraw = True
                    elif ev == 'ESC':
                        return None
                    elif ev == 'ENTER':
                        return items[selectable[sel_pos]]["id"]
                    elif isinstance(ev, tuple):
                        action, mx, my = ev
                        if action == 'HOVER':
                            update_hover_selection(my)
                        elif action == 'CLICK':
                            update_hover_selection(my)
                            if sx <= mx < sx + mw and sy <= my < sy + mh:
                                row = my - sy - 2
                                if 0 <= row < len(items) and items[row]["type"] == "item":
                                    return items[row]["id"]
                            else:
                                return None
    finally:
        sys.stdout.write("\033[?1006l\033[?1015l\033[?1003l\033[?1002l\033[?1000l\033[0m")
        sys.stdout.flush()

def kilo_input(prompt, redraw_callback, allow_esc=True):
    chars = []
    try:
        sys.stdout.write(f"{C_RESET}\033[?25l")
        tw, bw, m = redraw_callback()

        def draw_prompt():
            prefix = f" {prompt} "
            avail = max(1, bw - text_width(prefix))
            disp = ''.join(chars)
            if text_width(disp) > avail:
                while text_width(disp) > avail - 3 and disp:
                    disp = disp[1:]
                disp = "..." + disp
            spaces = max(0, bw - text_width(prefix) - text_width(disp))
            box_render = f"\r{m}{C_BLUE}▌{C_BG_INPUT}{C_GRAY}{prefix}{C_WHITE}{disp}{' ' * spaces}{C_RESET}\033[K"
            sys.stdout.write(box_render)
            if spaces > 0:
                sys.stdout.write(f"\033[{spaces}D")
            sys.stdout.flush()

        draw_prompt()
        sys.stdout.write(f"{C_WHITE}\033[?25h")
        sys.stdout.flush()
        last_size = get_term_width()
        
        with RawInput():
            while True:
                ev = get_event()
                curr_size = get_term_width()
                if curr_size != last_size:
                    last_size = curr_size
                    sys.stdout.write(f"{C_RESET}\033[?25l")
                    tw, bw, m = redraw_callback()
                    sys.stdout.write(f"{C_WHITE}\033[?25h")
                    draw_prompt()
                if ev == 'ESC':
                    if allow_esc:
                        sys.stdout.write(f"{C_RESET}\033[?25l")
                        return 'esc'
                elif ev == 'ENTER':
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    sys.stdout.write(f"{C_RESET}\033[?25l")
                    return ''.join(chars)
                elif ev == 'BACKSPACE':
                    if chars:
                        chars.pop()
                        draw_prompt()
                elif isinstance(ev, str) and len(ev) == 1:
                    chars.append(ev)
                    draw_prompt()
    except KeyboardInterrupt:
        sys.stdout.write(f"{C_RESET}\033[?1049l\033[?25h\n")
        sys.stdout.flush()
        sys.exit(0)
    except EOFError:
        sys.stdout.write(f"{C_RESET}\033[?25l")
        sys.stdout.flush()
        return 'esc' if allow_esc else ''

def is_esc(val):
    return val.lower() in ('esc', 'q', '\x1b', 'exit')

def draw_header(m, bw, title):
    spaces = " " * max(1, bw - text_width(title) - 3)
    print(f"{m}{C_WHITE}{C_BOLD}{title}{C_RESET}{spaces}{C_GRAY}esc{C_RESET}\n")

def draw_menu_item(m, num, text):
    print(f"{m}{C_YELLOW}{num}{C_RESET}  {C_WHITE}{text}{C_RESET}")

def draw_sys_item(m, bw, label, value):
    label_disp = label + "   "
    val_disp = truncate_text(value, bw - text_width(label_disp))
    print(f"{m}{C_WHITE}{label_disp}{C_RESET}{C_GRAY}{val_disp}{C_RESET}")

def settings_menu(lang, output_dir):
    while True:
        t = T[lang]

        def draw_bg():
            clear_screen(18)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["commands"])
            print(f"{m}{C_BLUE}{t['actions']}{C_RESET}")
            draw_menu_item(m, "1", t["start"])
            draw_menu_item(m, "2", t["settings"])
            print()
            print(f"{m}{C_BLUE}{t['system']}{C_RESET}")
            draw_sys_item(m, bw, t["output_path"], output_dir)
            print_tip(t["tip_main"], m, bw)

        items = [
            {"type": "category", "label": t["settings"]},
            {"type": "item", "id": "path", "label": t["change_path"]},
            {"type": "item", "id": "lang", "label": t["change_lang"]}
        ]
        
        choice = show_floating_modal(t["settings"], items, draw_bg)
        
        if not choice:
            break
        elif choice == 'path':
            def draw_path_bg():
                clear_screen(15)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["settings"])
                print()
                return tw, bw, m
                
            raw_path = kilo_input(t["new_path"], draw_path_bg)
            
            if not is_esc(raw_path) and raw_path:
                new_path = clean_path(raw_path)
                try:
                    os.makedirs(new_path, exist_ok=True)
                    output_dir = new_path
                    save_config(lang, output_dir)
                    kilo_input(f"{t['press_enter']}:", lambda: (draw_path_bg()[0:0] or print(f"{get_layout()[2]}{C_WHITE}{t['path_updated']}{C_RESET}\n") or get_layout()))
                except Exception as e:
                    kilo_input(f"{t['press_enter']}:", lambda: (draw_path_bg()[0:0] or print(f"{get_layout()[2]}{C_YELLOW}Error: {e}{C_RESET}\n") or get_layout()))
        elif choice == 'lang':
            lang_items = [
                {"type": "category", "label": t["language"]},
                {"type": "item", "id": "en", "label": "English"},
                {"type": "item", "id": "ru", "label": "Русский"},
                {"type": "item", "id": "zh", "label": "中文"}
            ]
            new_lang = show_floating_modal(t["change_lang"], lang_items, draw_bg)
            if new_lang:
                lang = new_lang
                save_config(lang, output_dir)

    return lang, output_dir

def run_script(lang, output_dir):
    t = T[lang]

    def draw_target():
        clear_screen(13)
        draw_logo()
        tw, bw, m = get_layout()
        draw_header(m, bw, t["target_dir"])
        print(f"{m}{C_BLUE}{t['input']}{C_RESET}")
        print(f"{m}{C_GRAY}{t['enter_path']}{C_RESET}\n")
        return tw, bw, m

    raw_path = kilo_input(t["path"], draw_target)

    if is_esc(raw_path):
        return

    paths = parse_dropped_paths(raw_path)

    if not paths:
        return

    base_dir = paths[0] if os.path.isdir(paths[0]) else os.path.dirname(paths[0])
    file_data = []
    seen = set()

    def process_scanned_paths(input_paths):
        for p in input_paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        full_p = os.path.join(root, f)
                        abs_p = os.path.abspath(full_p)
                        if abs_p not in seen and is_image_file(full_p):
                            seen.add(abs_p)
                            rel_p = os.path.relpath(full_p, base_dir)
                            file_data.append({"path": full_p, "name": rel_p, "selected": True, "supported": True})
            elif os.path.isfile(p):
                abs_p = os.path.abspath(p)
                if abs_p not in seen and is_image_file(p):
                    seen.add(abs_p)
                    rel_p = os.path.relpath(p, base_dir) if p.startswith(base_dir) else os.path.basename(p)
                    file_data.append({"path": p, "name": rel_p, "selected": True, "supported": True})

    process_scanned_paths(paths)

    if not file_data:
        kilo_input(
            f"{t['press_enter_return']}:",
            lambda: (clear_screen(15), draw_logo(), print(f"\n{get_layout()[2]}{C_YELLOW}{t['err_empty']}{C_RESET}\n"), get_layout())[-1]
        )
        return

    memory = load_memory()
    disabled = memory.get(os.path.abspath(base_dir), {}).get("disabled_files", [])

    for item in file_data:
        if item["name"] in disabled:
            item["selected"] = False

    page = 0
    per_page = 10
    exif_opts = [True, False, False, False] 

    while True:
        go_back_to_files = False
        
        while True:
            total_items = len(file_data)
            total_pages = max(1, (total_items + per_page - 1) // per_page)
            page = max(0, min(page, total_pages - 1))
            
            start_idx = page * per_page
            end_idx = start_idx + per_page
            visible_data = file_data[start_idx:end_idx]

            def draw_selection():
                clear_screen(20)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["select_files"])
                print(f"{m}{C_BLUE}{t['dir']}{C_RESET}\n{m}{C_WHITE}{truncate_text(base_dir, bw)}{C_RESET}\n")

                for i, item in enumerate(visible_data):
                    color = C_WHITE if item["selected"] else C_DARK_GRAY
                    print(f"{m}{color}{i + 1:<2}  {truncate_text(item['name'], bw - 6)}{C_RESET}")

                sel_count = sum(1 for i in file_data if i["selected"])
                print(f"\n{m}{C_GRAY}{t['selected']} {C_WHITE}{sel_count}{C_GRAY} {t['of']} {total_items}  |  Page {page + 1}/{total_pages}{C_RESET}")
                print_tip(t["tip_toggle"], m, bw)
                return tw, bw, m

            choice = kilo_input(t["toggle"], draw_selection).strip().lower()

            if is_esc(choice):
                return

            if choice == '0':
                if not any(i["selected"] for i in file_data):
                    kilo_input(f"{t['press_enter_return']}:", lambda: (clear_screen(15), draw_logo(), print(f"\n{get_layout()[2]}{C_YELLOW}{t['err_no_selected']}{C_RESET}\n"), get_layout())[-1])
                    continue
                break
            elif choice == 'n':
                page += 1
            elif choice == 'p':
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(visible_data):
                    real_idx = start_idx + idx
                    file_data[real_idx]["selected"] = not file_data[real_idx]["selected"]
            elif choice:
                new_paths = parse_dropped_paths(choice)
                if new_paths:
                    process_scanned_paths(new_paths)

        while True:
            def draw_exif():
                clear_screen(18)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["exif_title"])
                
                options = [
                    t["exif_all"],
                    t["exif_gps"],
                    t["exif_cam"],
                    t["exif_date"]
                ]
                
                for i, opt_text in enumerate(options):
                    is_sel = exif_opts[i]
                    prefix = f"{C_WHITE}[{C_YELLOW}*{C_WHITE}]" if is_sel else f"{C_DARK_GRAY}[ ]"
                    color = C_WHITE if is_sel else C_GRAY
                    print(f"{m}{prefix} {C_YELLOW}{i+1}{C_RESET} {color}{opt_text}{C_RESET}")
                
                print_tip(t["tip_exif"], m, bw)
                return tw, bw, m

            choice = kilo_input("Toggle (0 to start):", draw_exif).strip()
            
            if is_esc(choice):
                go_back_to_files = True
                break
            if choice == '0':
                break
            
            if choice in ['1', '2', '3', '4']:
                idx = int(choice) - 1
                if choice == '1':
                    exif_opts = [True, False, False, False]
                else:
                    if exif_opts[0]:
                        exif_opts[0] = False
                        exif_opts[idx] = True
                    else:
                        exif_opts[idx] = not exif_opts[idx]
                        if not any(exif_opts):
                            exif_opts[0] = True
                            
        if go_back_to_files:
            continue
            
        break

    selected_files = [i for i in file_data if i["selected"]]
    save_memory(base_dir, [i["name"] for i in file_data if not i["selected"]])
    os.makedirs(output_dir, exist_ok=True)
    errors = []

    for item in selected_files:
        try:
            out_path = os.path.join(output_dir, item["name"])
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            img = Image.open(item["path"])
            ext = item["path"].lower().split('.')[-1]
            
            if ext in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            is_animated = getattr(img, "is_animated", False)

            if exif_opts[0]:
                img.save(out_path, save_all=is_animated)
            else:
                exif = img.getexif()
                if exif:
                    if exif_opts[1] and 34853 in exif:
                        del exif[34853]
                        
                    if exif_opts[2]:
                        for tag in [271, 272, 315]:
                            if tag in exif: del exif[tag]
                        if 34665 in exif:
                            ifd = exif.get_ifd(34665)
                            for tag in [33434, 33437, 34850, 34855, 37386, 41989, 42036]:
                                if tag in ifd: del ifd[tag]
                            exif[34665] = ifd

                    if exif_opts[3]:
                        if 306 in exif: del exif[306]
                        if 34665 in exif:
                            ifd = exif.get_ifd(34665)
                            for tag in [36867, 36868]:
                                if tag in ifd: del ifd[tag]
                            exif[34665] = ifd
                            
                    img.save(out_path, exif=exif, save_all=is_animated)
                else:
                    img.save(out_path, save_all=is_animated)

        except Exception as e:
            errors.append(f"{os.path.basename(item['path'])}: {str(e)}")

    def draw_result():
        clear_screen(15)
        draw_logo()
        tw, bw, m = get_layout()
        if errors:
            print(f"\n{m}{C_YELLOW}{t['err_save']}{C_RESET}")
            for err in errors[:5]:
                print(f"{m}{C_GRAY}{truncate_text(err, bw)}{C_RESET}")
            if len(errors) > 5:
                print(f"{m}{C_GRAY}... and {len(errors)-5} more{C_RESET}")
        else:
            print(f"\n{m}{C_WHITE}{t['success_msg']}{C_RESET}\n")
        return tw, bw, m

    kilo_input(f"{t['press_enter_return']}:", lambda: (draw_result())[-1])

def main_menu(lang, output_dir):
    while True:
        t = T[lang]

        def draw_main():
            clear_screen(18)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["commands"])
            print(f"{m}{C_BLUE}{t['actions']}{C_RESET}")
            draw_menu_item(m, "1", t["start"])
            draw_menu_item(m, "2", t["settings"])
            print(f"\n{m}{C_BLUE}{t['system']}{C_RESET}")
            draw_sys_item(m, bw, t["output_path"], output_dir)
            print_tip(t["tip_main"], m, bw)
            return tw, bw, m

        choice = kilo_input(t["action"], draw_main, allow_esc=False)

        if choice == '1':
            run_script(lang, output_dir)
        elif choice == '2':
            lang, output_dir = settings_menu(lang, output_dir)

if __name__ == "__main__":
    sys.stdout.write("\033[?1049h\033[H")
    sys.stdout.flush()
    try:
        l, o = load_config()
        main_menu(l, o)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(f"{C_RESET}\033[?1049l\033[?25h\n")
        sys.stdout.flush()