import os
import time
from datetime import timedelta, datetime
from threading import Thread, Lock

import psutil
import pyautogui
import pyscreeze
import requests
import win32con
import win32gui
import win32process

from src import config

pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False
UTIL_DIR = os.path.dirname(os.path.abspath(__file__))

PROCNAME = "exefile.exe"
MOUSE_LEFT = pyautogui.LEFT
MOUSE_RIGHT = pyautogui.RIGHT

previousCursorLocation = (0, 0)
failsafeTimers = dict()
fatalErrorCount = 0


def get_path(filepath):
    util_dir_split = UTIL_DIR.split(os.sep)
    filepath_split = filepath.split("/")
    return os.path.join(util_dir_split[0], os.sep, *(util_dir_split[1:-2] + filepath_split))


def log_console(*args, **kwargs):
    """
    Deprecated, use log() instead
    """
    t = time.localtime()
    time_string = time.strftime("%Y/%m/%d %H:%M:%S: ", t)
    print(time_string + " ".join(map(str, args)), **kwargs)


def init_logger(log_file_path):
    config.LOG_FILENAME = log_file_path
    log("---------------------------------- Logging Initialized ----------------------------------", gap=1)


def log(log_message, log_to_console=True, gap=0):
    log_message = str(log_message)
    t = time.localtime()
    time_string = time.strftime("%Y/%m/%d %H:%M:%S: ", t)

    if log_to_console:
        print(time_string + log_message)

    with open(get_path(config.LOG_FILENAME), "a") as f:
        f.write("\n" * (gap + 1) + time_string + log_message)


def move_cursor(coordinates: (int, int)):
    global previousCursorLocation
    while previousCursorLocation != win32gui.GetCursorPos():
        previousCursorLocation = win32gui.GetCursorPos()
        time.sleep(2)

    pyautogui.moveTo(coordinates[0], coordinates[1])

    previousCursorLocation = win32gui.GetCursorPos()


def click(target, button=pyautogui.LEFT, pos_x=0.5, pos_y=0.5, wait_before=0.1, wait_after=0.1):
    move_cursor(target.get_center(pos_x, pos_y))
    time.sleep(wait_before)
    pyautogui.mouseDown(button=button, _pause=False)
    time.sleep(0.05)
    pyautogui.mouseUp(button=button, _pause=False)
    time.sleep(wait_after)


def left_click(target):
    """
    deprecated use click() instead
    """
    if type(target).__name__ == "UITreeNode":
        target = target.get_center()
    click_coordinate(target, left_button=True)


def right_click(target):
    """
    deprecated use click() instead
    """
    if type(target).__name__ == "UITreeNode":
        target = target.get_center()
    click_coordinate(target, left_button=False)


def click_coordinate(coordinates: (int, int), left_button=True):
    """
    deprecated use click() instead
    """
    button = pyautogui.LEFT if left_button else pyautogui.RIGHT

    move_cursor(coordinates)
    time.sleep(0.2)
    pyautogui.mouseDown(button=button)
    time.sleep(0.1)
    pyautogui.mouseUp(button=button)
    time.sleep(0.5)


def drag_and_drop(
        start_coordinates: (int, int),
        end_coordinates: (int, int),
        left_button=True
):
    button = pyautogui.LEFT if left_button else pyautogui.RIGHT

    move_cursor(start_coordinates)
    time.sleep(0.2)
    pyautogui.mouseDown(button=button)
    time.sleep(0.2)
    move_cursor(end_coordinates)
    time.sleep(0.2)
    pyautogui.mouseUp(button=button)
    time.sleep(0.2)


def failsafe(delta, msg="", timer_name=""):
    global failsafeTimers
    d = timedelta(seconds=delta)
    if datetime.now() - failsafeTimers.get(timer_name) > d:
        raise Exception(f"Timeout {msg}")


def start_failsafe(timer_name=""):
    global failsafeTimers
    failsafeTimers.update({timer_name: datetime.now()})


def get_pid():
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            return proc.pid


def find_window_for_pid(pid):
    result = None

    def callback(hwnd, _):
        nonlocal result
        _tid, c_pid = win32process.GetWindowThreadProcessId(hwnd)
        if c_pid == pid:
            result = hwnd
            return False
        return True

    win32gui.EnumWindows(callback, None)
    return result


def close_client():
    log_console("Closing client")
    eve = win32gui.FindWindow(None, fr"EVE - {config.CHARACTER_NAME}")
    if eve != 0:
        win32gui.PostMessage(eve, win32con.WM_CLOSE, 0, 0)
    else:
        eve = win32gui.FindWindow("trinityWindow", "EVE")
        if eve != 0:
            win32gui.PostMessage(eve, win32con.WM_CLOSE, 0, 0)


def start_game(ui_tree):
    log_console("Starting client")
    start_failsafe()
    btn_play_now = pyautogui.locateOnScreen(get_path("images/btn_play_now.png"), grayscale=True, confidence=0.7)
    while not btn_play_now:
        time.sleep(5)
        btn_play_now = pyautogui.locateOnScreen(get_path("images/btn_complete_mission.png"), grayscale=True,
                                                confidence=0.7)
        failsafe(60, "Finding play button")
    left_click((btn_play_now[0] + 15, btn_play_now[1] + 15))
    trial_count = 1
    while True:
        log_console(f"Waiting for client window {trial_count}")
        time.sleep(5)
        eve = win32gui.FindWindow("trinityWindow", "EVE")
        if eve != 0:
            break
        trial_count += 1
        if trial_count > 10:
            raise Exception("Can't launch game")
    # win32gui.MoveWindow(eve, 1713, 0, 1734, 1407, True)  # todo remove hard coded values
    win32gui.MoveWindow(eve, -7, 0, 1727, 1407, True)
    time.sleep(1)
    start_failsafe()
    while win32gui.FindWindow(None, fr"EVE - {config.CHARACTER_NAME}") == 0:
        win32gui.SetForegroundWindow(eve)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(9)
        failsafe(60)
    while not ui_tree.find_node({'_name': 'EVEMenuIcon'}, refresh=True):
        log_console(f"Waiting for neo-com {trial_count}")
        trial_count += 1
        if trial_count > 10:
            raise Exception("Can't find neo-com")
        time.sleep(5)
    time.sleep(5)
    start_img = pyautogui.screenshot()
    start_img.save(fr"startImg{fatalErrorCount}.png")
    time.sleep(5)


def wait_for_truthy(func, timeout, check_interval=0.5):
    start = time.time()
    first_iter = True
    while time.time() - start < timeout or first_iter:
        first_iter = False
        func_start = time.time()
        return_value = func()
        if return_value:
            return return_value
        time.sleep(max(0.0, check_interval - (time.time() - func_start)))
    return None


def inactivity_watchdog(timer_dict, lock, max_inactivity_time, check_interval=60):
    log("Inactivity watchdog started")
    requests.post(
        config.DISCORD_NOTIFICATION_WEBHOOK_URL,
        json={"content": f"<@&{config.DISCORD_NOTIFICATION_ROLE_ID}> Inactivity watchdog started"}
    )
    notification_sent = False
    while True:
        time.sleep(check_interval)
        with lock:
            elapsed = time.time() - timer_dict["timer"]
        if elapsed >= max_inactivity_time:
            if notification_sent:
                continue

            log(f"Inactivity time limit of {max_inactivity_time} seconds exceeded! Sending HTTP notification...")
            requests.post(
                config.DISCORD_NOTIFICATION_WEBHOOK_URL,
                json={
                    "content": f"<@&{config.DISCORD_NOTIFICATION_ROLE_ID}> "
                               f"Inactivity time limit of {max_inactivity_time} seconds exceeded!"
                }
            )
            notification_sent = True
        else:
            notification_sent = False


def start_inactivity_watchdog(max_inactivity_time):
    timer_dict = {"timer": time.time()}
    lock = Lock()

    Thread(target=inactivity_watchdog, args=(timer_dict, lock, max_inactivity_time), daemon=True).start()

    return timer_dict, lock


def reset_inactivity_timer(timer_dict, lock):
    with lock:
        timer_dict["timer"] = time.time()
