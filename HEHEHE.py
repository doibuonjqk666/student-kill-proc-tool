# -*- coding: utf-8 -*-

"""
Student Process Terminator -  HEHEHE
Tự động tìm và dừng mọi process Student.exe cùng với các tiến trình con.
"""

import subprocess
import sys
import time
import ctypes
import psutil
import colorama
import keyboard
import os
import logging
import threading
from datetime import datetime
from colorama import Fore, Style
from typing import List, Set, Dict

# Cấu hình logging
logging.basicConfig(
    filename='HEHEHE.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Đặt encoding UTF-8 cho console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

colorama.init()

# Constants
STUDENT_EXE = "Student.exe"
STUDENT_PATH = r"C:\Program Files (x86)\Oneclass\Student.exe"
VERSION = "1.0.0"
HOTKEY_COOLDOWN = 0.5 

# Biến điều khiển vòng lặp chính
running = True
paused = False  
last_hotkey_time: Dict[str, float] = {} 
hotkey_lock = threading.Lock()  #
hidden = False  

def is_admin() -> bool:
    """Kiểm tra quyền admin"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra quyền admin: {e}")
        return False

def print_banner():
    """In banner đẹp hơn với version"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
║ {Fore.YELLOW}                         HEHEHE v{VERSION}                        {Fore.CYAN}║
║ {Fore.GREEN}                     https://url.spa/hacker                   {Fore.CYAN}║
║ {Fore.MAGENTA}                         Made By Human                        {Fore.CYAN}║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_menu():
    """In menu với màu sắc đẹp hơn"""
    print(f"\n{Fore.RED}╔═══════════════════════════════════════════════════════════════╗")
    print(f"║ {Fore.YELLOW}                        MENU ĐIỀU KHIỂN                       {Fore.RED}║")
    print(f"╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}► Nhấn 'T' để tìm và terminate Student.exe{Style.RESET_ALL}")
    print(f"{Fore.CYAN}► Nhấn 'O' để mở lại Student.exe{Style.RESET_ALL}")
    print(f"{Fore.CYAN}► Nhấn 'R' để refresh màn hình{Style.RESET_ALL}")
    print(f"{Fore.CYAN}► Nhấn 'Q' để thoát chương trình{Style.RESET_ALL}")
    print(f"{Fore.CYAN}► Nhấn 'Page Up' để tạm dừng/tiếp tục chương trình{Style.RESET_ALL}")
    print(f"{Fore.CYAN}► Nhấn 'Page Down' để ẩn/hiện cửa sổ console (chạy ngầm){Style.RESET_ALL}\n")

def get_student_processes() -> List[psutil.Process]:
    """Lấy danh sách các process Student.exe"""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'ppid']):
            try:
                if proc.info['name'].lower() == STUDENT_EXE.lower():
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logging.error(f"Lỗi khi tìm process: {e}")
    return processes

def kill_student_processes() -> int:
    """Kill tất cả process Student.exe và process con"""
    target = STUDENT_EXE
    print(f"\n{Fore.CYAN}V Đang tìm các tiến trình {target}...{Style.RESET_ALL}")
    total_killed = 0
    terminated: Set[int] = set()

    processes = get_student_processes()

    if not processes:
        print(f"{Fore.YELLOW}Không tìm thấy tiến trình {target}.{Style.RESET_ALL}")
        return 0

    for proc in processes:
        try:
            queue = [proc]
            while queue:
                current = queue.pop(0)
                if current.pid in terminated:
                    continue
                try:
                    children = current.children(recursive=False)
                    queue.extend(children)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                try:
                    current.terminate()
                    print(f"{Fore.YELLOW}V Đã dừng {current.name()} (PID: {current.pid}){Style.RESET_ALL}")
                    terminated.add(current.pid)
                    total_killed += 1
                    logging.info(f"Đã terminate process {current.name()} (PID: {current.pid})")
                except Exception as e:
                    logging.error(f"Lỗi khi terminate process {current.pid}: {e}")
        except Exception as e:
            logging.error(f"Lỗi khi xử lý process {proc.pid}: {e}")

    time.sleep(2)

    # Force kill các process còn sót lại
    for pid in terminated:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            print(f"{Fore.RED}! Force kill {proc.name()} (PID: {proc.pid}){Style.RESET_ALL}")
            logging.info(f"Force kill process {proc.name()} (PID: {proc.pid})")
        except:
            pass

    print(f"\n{Fore.GREEN}V Đã kết thúc {total_killed} tiến trình liên quan đến Student.exe{Style.RESET_ALL}")
    return total_killed

def check_hotkey_cooldown(hotkey: str) -> bool:
    """Kiểm tra cooldown của hotkey"""
    with hotkey_lock:
        current_time = time.time()
        if hotkey in last_hotkey_time:
            if current_time - last_hotkey_time[hotkey] < HOTKEY_COOLDOWN:
                return False
        last_hotkey_time[hotkey] = current_time
        return True

def safe_hotkey_handler(func):
    """Decorator để xử lý hotkey an toàn"""
    def wrapper(*args, **kwargs):
        if not check_hotkey_cooldown(func.__name__):
            return
        try:
            func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Lỗi khi xử lý hotkey {func.__name__}: {e}")
            print(f"{Fore.RED}X Lỗi khi xử lý lệnh: {e}{Style.RESET_ALL}")
    return wrapper

@safe_hotkey_handler
def on_t_press():
    """Xử lý khi nhấn phím T"""
    if paused:
        print(f"{Fore.YELLOW}! Chương trình đang tạm dừng. Nhấn Page Up để tiếp tục.{Style.RESET_ALL}")
        return
    killed = kill_student_processes()
    if killed == 0:
        print(f"{Fore.YELLOW}Không có tiến trình nào cần terminate.{Style.RESET_ALL}")
    print_menu()

@safe_hotkey_handler
def on_o_press():
    """Xử lý khi nhấn phím O"""
    if paused:
        print(f"{Fore.YELLOW}! Chương trình đang tạm dừng. Nhấn Page Up để tiếp tục.{Style.RESET_ALL}")
        return
    if os.path.exists(STUDENT_PATH):
        try:
            subprocess.Popen([STUDENT_PATH], shell=True)
            print(f"{Fore.GREEN}V Đã mở Student.exe thành công.{Style.RESET_ALL}")
            logging.info("Đã mở Student.exe thành công")
        except Exception as e:
            print(f"{Fore.RED}X Không thể mở file: {e}{Style.RESET_ALL}")
            logging.error(f"Lỗi khi mở Student.exe: {e}")
    else:
        print(f"{Fore.RED}X Không tìm thấy file: {STUDENT_PATH}{Style.RESET_ALL}")
        logging.error(f"Không tìm thấy file Student.exe tại {STUDENT_PATH}")
    print_menu()

@safe_hotkey_handler
def on_r_press():
    """Xử lý khi nhấn phím R"""
    if paused:
        print(f"{Fore.YELLOW}! Chương trình đang tạm dừng. Nhấn Page Up để tiếp tục.{Style.RESET_ALL}")
        return
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    print_menu()

@safe_hotkey_handler
def on_q_press():
    """Xử lý khi nhấn phím Q"""
    if paused:
        print(f"{Fore.YELLOW}! Chương trình đang tạm dừng. Nhấn Page Up để tiếp tục.{Style.RESET_ALL}")
        return
    global running
    print(f"{Fore.GREEN}V Đang thoát chương trình...{Style.RESET_ALL}")
    logging.info("Đang thoát chương trình")
    keyboard.unhook_all_hotkeys()
    running = False

@safe_hotkey_handler
def on_pause_press():
    """Xử lý khi nhấn phím Page Up"""
    global paused
    paused = not paused
    if paused:
        print(f"{Fore.YELLOW}! Chương trình đã tạm dừng. Nhấn Page Up để tiếp tục.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}-> Tất cả các chức năng khác đã bị vô hiệu hóa.{Style.RESET_ALL}")
        logging.info("Chương trình đã tạm dừng")
    else:
        print(f"{Fore.GREEN}V Chương trình đã tiếp tục hoạt động.{Style.RESET_ALL}")
        logging.info("Chương trình đã tiếp tục hoạt động")
    print_menu()

@safe_hotkey_handler
def on_h_press():
    """Xử lý khi nhấn phím Page Down để ẩn/hiện console"""
    global hidden
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            if not hidden:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
                hidden = True
                logging.info("Đã ẩn cửa sổ console, chương trình chạy ngầm.")
            else:
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # 5 = SW_SHOW
                hidden = False
                logging.info("Đã hiện lại cửa sổ console.")
    except Exception as e:
        print(f"{Fore.RED}X Không thể ẩn/hiện console: {e}{Style.RESET_ALL}")
        logging.error(f"Lỗi khi ẩn/hiện console: {e}")

def register_hotkeys():
    """Đăng ký các hotkey với xử lý lỗi"""
    try:
        keyboard.add_hotkey('t', on_t_press)
        keyboard.add_hotkey('o', on_o_press)
        keyboard.add_hotkey('r', on_r_press)
        keyboard.add_hotkey('q', on_q_press)
        keyboard.add_hotkey('page up', on_pause_press)
        keyboard.add_hotkey('page down', on_h_press)
        logging.info("Đã đăng ký hotkeys thành công")
    except Exception as e:
        logging.error(f"Lỗi khi đăng ký hotkeys: {e}")
        print(f"{Fore.RED}X Lỗi khi đăng ký hotkeys: {e}{Style.RESET_ALL}")
        sys.exit(1)

def main():
    """Hàm main chính"""
    try:
        print_banner()

        if not is_admin():
            print(f"{Fore.YELLOW}! Chạy không có quyền admin. Một số tiến trình có thể không bị terminate.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}-> Khuyên dùng: Chuột phải -> 'Run as administrator'{Style.RESET_ALL}\n")
            logging.warning("Chương trình chạy không có quyền admin")

        print_menu()

        register_hotkeys()

        logging.info("Chương trình đã khởi động thành công")

        while running:
            if not paused: 
                time.sleep(0.1)
            else:
                time.sleep(0.5)  # Giảm CPU usage khi đang tạm dừng

        sys.exit(0)

    except Exception as e:
        error_msg = f"Đã xảy ra lỗi: {e}"
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        logging.error(error_msg)
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()
