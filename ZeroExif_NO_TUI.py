import os
import sys
import json
import textwrap
import shlex
import urllib.parse
import time
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

if sys.platform == 'win32':
    os.system('')

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
        "tip_toggle": "1-10 to toggle, 'n'/'p' for pages, 0 to start, or Drag & Drop more",
        "toggle": "Toggle/Page:",
        "err_no_selected": "No images selected.",
        "success": "Success",
        "success_msg": "EXIF data successfully removed.",
        "output_loc": "Output location",
        "err_save": "Save error(s) occurred:"
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
        "tip_toggle": "1-10 для выбора, 'n'/'p' для страниц, 0 для старта, или перетащите еще",
        "toggle": "Выбор/Стр:",
        "err_no_selected": "Фотографии не выбраны.",
        "success": "Успешно",
        "success_msg": "Метаданные успешно удалены.",
        "output_loc": "Место сохранения",
        "err_save": "Возникли ошибки при сохранении:"
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
        "tip_toggle": "1-10 切换, 'n'/'p' 翻页, 0 开始, 或拖放更多照片",
        "toggle": "切换/翻页:",
        "err_no_selected": "未选择任何照片。",
        "success": "成功",
        "success_msg": "EXIF 数据已成功删除。",
        "output_loc": "输出位置",
        "err_save": "保存时发生错误:"
    }
}

def clean_path(p):
    if not p:
        return p
    p = p.strip(' "\'\r\n\t')
    if p.startswith("file://"):
        p = p[7:]
        p = urllib.parse.unquote(p)
        if sys.platform == 'win32' and p.startswith('/') and len(p) > 2 and p[2] == ':':
            p = p[1:]
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

def truncate_text(text, max_len):
    max_len = max(0, max_len)
    if len(text) <= max_len:
        return text
    if max_len < 4:
        return "..."[:max_len]
    return text[:max_len - 3] + "..."

def draw_logo():
    ASCII_LOGO = [
        "▄▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄   ▄▄▄    ▄▄▄▄▄ ▄▄ ▄▄ ▄▄ ▄▄▄▄▄",
        "  ▄█▀ ██▄▄  ██▄█▄ ██▀██   ██▄▄  ▀█▄█▀ ██ ██▄▄ ",
        "▄██▄▄ ██▄▄▄ ██ ██ ▀███▀   ██▄▄▄ ██ ██ ██ ██   ",
        "~~~~~ ~~~~~ ~~ ~~  ~~~    ~~~~~ ~~ ~~ ~~ ~~   "
    ]
    C_SHADOW_FG = "\033[38;2;90;90;40m"
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

def kilo_input(prompt, redraw_callback, allow_esc=True):
    chars = []
    try:
        sys.stdout.write(f"{C_RESET}\033[?25l")
        tw, bw, m = redraw_callback()

        def draw_prompt():
            prefix = f" {prompt} "
            avail = max(1, bw - len(prefix))
            disp = ''.join(chars)
            if len(disp) > avail:
                disp = "..." + disp[-(avail - 3):] if avail > 3 else disp[-avail:]
            spaces = max(0, bw - len(prefix) - len(disp))
            box_render = f"\r{m}{C_BLUE}▌{C_BG_INPUT}{C_GRAY}{prefix}{C_WHITE}{disp}{' ' * spaces}{C_RESET}\033[K"
            sys.stdout.write(box_render)
            if spaces > 0:
                sys.stdout.write(f"\033[{spaces}D")
            sys.stdout.flush()

        draw_prompt()
        last_size = get_term_width()

        if sys.platform == 'win32':
            import msvcrt
            while True:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch == '\x1b':
                        if allow_esc:
                            return 'esc'
                    elif ch in ('\r', '\n'):
                        sys.stdout.write('\n')
                        return ''.join(chars)
                    elif ch == '\b':
                        if chars:
                            chars.pop()
                            draw_prompt()
                    elif ch == '\x03':
                        raise KeyboardInterrupt
                    elif ch in ('\x00', '\xe0'):
                        msvcrt.getwch()
                    else:
                        chars.append(ch)
                        draw_prompt()
                else:
                    curr_size = get_term_width()
                    if curr_size != last_size:
                        last_size = curr_size
                        tw, bw, m = redraw_callback()
                        draw_prompt()
                    time.sleep(0.01)
        else:
            import tty
            import termios
            import select
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if r:
                        chunk = os.read(fd, 4096).decode('utf-8', 'replace')
                        i = 0
                        while i < len(chunk):
                            ch = chunk[i]
                            if ch == '\x1b':
                                if i + 1 < len(chunk) and chunk[i + 1] in ('[', 'O'):
                                    i += 2
                                    while i < len(chunk) and chunk[i] not in 'ABCDEFGHJKMPRSTVXZcfghinqrstuv':
                                        i += 1
                                else:
                                    if allow_esc:
                                        return 'esc'
                            elif ch in ('\n', '\r'):
                                sys.stdout.write('\n')
                                return ''.join(chars)
                            elif ch in ('\x7f', '\b'):
                                if chars:
                                    chars.pop()
                            elif ch == '\x03':
                                raise KeyboardInterrupt
                            else:
                                chars.append(ch)
                            i += 1
                        draw_prompt()
                    else:
                        curr_size = get_term_width()
                        if curr_size != last_size:
                            last_size = curr_size
                            tw, bw, m = redraw_callback()
                            draw_prompt()
                        time.sleep(0.01) 
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
    finally:
        sys.stdout.write(f"{C_RESET}\033[?25h\033[K")
        sys.stdout.flush()

def is_esc(val):
    return val.lower() in ('esc', 'q', '\x1b')

def draw_header(m, bw, title):
    spaces = " " * max(1, bw - len(title) - 3)
    print(f"{m}{C_WHITE}{C_BOLD}{title}{C_RESET}{spaces}{C_GRAY}esc{C_RESET}\n")

def draw_menu_item(m, num, text):
    print(f"{m}{C_YELLOW}{num}{C_RESET}  {C_WHITE}{text}{C_RESET}")

def draw_sys_item(m, bw, label, value):
    label_disp = label + "   "
    val_disp = truncate_text(value, bw - len(label_disp))
    print(f"{m}{C_WHITE}{label_disp}{C_RESET}{C_GRAY}{val_disp}{C_RESET}")

def settings_menu(lang, output_dir):
    while True:
        t = T[lang]

        def draw_main():
            clear_screen(15)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["settings"])
            print(f"{m}{C_BLUE}{t['actions']}{C_RESET}")
            draw_menu_item(m, "1", t["change_path"])
            draw_menu_item(m, "2", t["change_lang"])
            print()
            print_tip(t["tip_main"], m, bw)
            return tw, bw, m

        choice = kilo_input(t["action"], draw_main)

        if is_esc(choice):
            break
        elif choice == '1':
            def draw_path():
                clear_screen(15)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["settings"])
                return tw, bw, m

            raw_path = kilo_input(t["new_path"], draw_path)

            if not is_esc(raw_path) and raw_path:
                new_path = clean_path(raw_path)
                try:
                    os.makedirs(new_path, exist_ok=True)
                    output_dir = new_path
                    save_config(lang, output_dir)
                    kilo_input(
                        f"{t['press_enter']}:",
                        lambda: (
                            clear_screen(15),
                            draw_logo(),
                            print(f"\n{get_layout()[2]}{C_WHITE}{t['path_updated']}{C_RESET}\n"),
                            get_layout()
                        )[-1]
                    )
                except Exception as e:
                    kilo_input(
                        f"{t['press_enter']}:",
                        lambda: (
                            clear_screen(15),
                            draw_logo(),
                            print(f"\n{get_layout()[2]}{C_YELLOW}{e}{C_RESET}\n"),
                            get_layout()
                        )[-1]
                    )
        elif choice == '2':
            def draw_lang():
                clear_screen(15)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["settings"])
                print(f"\n{m}{C_WHITE}1 - English, 2 - Русский, 3 - 中文{C_RESET}\n")
                return tw, bw, m

            l_choice = kilo_input("Language:", draw_lang)

            if l_choice in ['1', '2', '3']:
                lang = ['en', 'ru', 'zh'][int(l_choice) - 1]
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

        choice = kilo_input(t["toggle"], draw_selection).strip()

        if is_esc(choice):
            return

        if choice == '0':
            break
        elif choice.lower() == 'n':
            page += 1
        elif choice.lower() == 'p':
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

    selected_files = [i for i in file_data if i["selected"]]

    if not selected_files:
        return

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