import os
import time
from datetime import timedelta, datetime
from typing import Union, Tuple

import psutil
import pyautogui
import pyscreeze
import win32api
import win32con
import win32gui
import win32process

from src import config
from src.utils.ui_tree import UITreeNode, UITree

pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False
UTIL_DIR = os.path.dirname(os.path.abspath(__file__))

PROCNAME = "exefile.exe"
MOUSE_LEFT = False
MOUSE_RIGHT = True

previousCursorLocation = (0, 0)
failsafeTimers = dict()
fatalErrorCount = 0


def get_path(filepath):
    util_dir_split = UTIL_DIR.split(os.sep)
    filepath_split = filepath.split("/")
    return os.path.join(util_dir_split[0], os.sep, *(util_dir_split[1:-2] + filepath_split))


def log_console(*args, **kwargs):
    t = time.localtime()
    time_string = time.strftime("%Y/%m/%d %H:%M:%S: ", t)
    print(time_string + " ".join(map(str, args)), **kwargs)


def log(log_message):
    t = time.localtime()
    time_string = time.strftime("%Y/%m/%d %H:%M:%S: ", t)
    with open(get_path(config.LOG_FILENAME), "a") as f:
        f.write("\n" + time_string + log_message)


def move_cursor(coordinates: (int, int)):
    global previousCursorLocation
    while previousCursorLocation != win32gui.GetCursorPos():
        previousCursorLocation = win32gui.GetCursorPos()
        time.sleep(2)

    win32api.SetCursorPos(coordinates)

    previousCursorLocation = win32gui.GetCursorPos()


def click(target: "UITreeNode", button=MOUSE_LEFT, pos_x=0.5, pos_y=0.5):
    down_event, up_event = (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP) \
        if button \
        else (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP)

    move_cursor(target.get_center(pos_x, pos_y))
    time.sleep(0.1)
    win32api.mouse_event(down_event, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(up_event, 0, 0)
    time.sleep(0.1)


def left_click(target: Union[Tuple[int, int], 'UITreeNode']):
    """
    deprecated use click() instead
    """
    if type(target) == UITreeNode:
        target = target.get_center()
    click_coordinate(target, left_button=True)


def right_click(target: Union[Tuple[int, int], 'UITreeNode']):
    """
    deprecated use click() instead
    """
    if type(target) == UITreeNode:
        target = target.get_center()
    click_coordinate(target, left_button=False)


def click_coordinate(coordinates: (int, int), left_button=True):
    """
    deprecated use click() instead
    """
    down_evnt = win32con.MOUSEEVENTF_LEFTDOWN \
        if left_button \
        else win32con.MOUSEEVENTF_RIGHTDOWN
    up_evnt = win32con.MOUSEEVENTF_LEFTUP \
        if left_button \
        else win32con.MOUSEEVENTF_RIGHTUP

    move_cursor(coordinates)
    time.sleep(0.2)
    win32api.mouse_event(down_evnt, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(up_evnt, 0, 0)
    time.sleep(0.5)


def drag_and_drop(
        start_coordinates: (int, int),
        end_coordinates: (int, int),
        left_button=True
):
    down_evnt = win32con.MOUSEEVENTF_LEFTDOWN \
        if left_button \
        else win32con.MOUSEEVENTF_RIGHTDOWN
    up_evnt = win32con.MOUSEEVENTF_LEFTUP \
        if left_button \
        else win32con.MOUSEEVENTF_RIGHTUP

    move_cursor(start_coordinates)
    time.sleep(0.5)
    win32api.mouse_event(down_evnt, 0, 0)
    time.sleep(0.5)
    move_cursor(end_coordinates)
    time.sleep(0.5)
    win32api.mouse_event(up_evnt, 0, 0)


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


def start_game():
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
    while not UITree.instance().find_node({'_name': 'EVEMenuIcon'}, refresh=True):
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
    while time.time() - start < timeout:
        func_start = time.time()
        return_value = func()
        if return_value:
            return return_value
        time.sleep(max(0.0, check_interval - (time.time() - func_start)))
    return None
