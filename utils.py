import time
from datetime import timedelta, datetime
from typing import Union, Tuple

import pyautogui
import win32api
import win32con
import win32gui

from interface import UITree, UITreeNode

import pyscreeze
pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False

LOG_FILENAME = "data/logMissions.txt"
CHARACTER_NAME = "Ahonen Yatolila"
AGENT_NAME = "vairosen"  # lvl3
# AGENT_NAME = "naninen" # lvl4

previousCursorLocation = (0, 0)
failsafeTimers = []
fatalErrorCount = 0


def log_console(*args, **kwargs):
    t = time.localtime()
    time_string = time.strftime("%Y/%m/%d %H:%M:%S: ", t)
    print(time_string + " ".join(map(str, args)), **kwargs)


def log(log_message):
    t = time.localtime()
    time_string = time.strftime("%Y/%m/%d %H:%M:%S: ", t)
    with open(LOG_FILENAME, "a") as f:
        f.write("\n" + time_string + log_message)


def move_cursor(coordinates: (int, int)):
    global previousCursorLocation
    while previousCursorLocation != win32gui.GetCursorPos():
        previousCursorLocation = win32gui.GetCursorPos()
        time.sleep(2)

    win32api.SetCursorPos(coordinates)

    previousCursorLocation = win32gui.GetCursorPos()


def left_click(target: Union[Tuple[int, int], 'UITreeNode']):
    if type(target) == UITreeNode:
        target = target.get_center()
    click(target, left_button=True)


def right_click(target: Union[Tuple[int, int], 'UITreeNode']):
    if type(target) == UITreeNode:
        target = target.get_center()
    click(target, left_button=False)


def click(coordinates: (int, int), left_button=True):
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


def failsafe(delta, msg="", timer_index=0):
    global failsafeTimers
    d = timedelta(seconds=delta)
    if datetime.now() - failsafeTimers[timer_index] > d:
        raise Exception(f"Timeout {msg}")


def start_failsafe(timer_index=0):
    global failsafeTimers
    if timer_index >= len(failsafeTimers):
        failsafeTimers.extend([datetime.now()] * (timer_index - len(failsafeTimers) + 1))
    else:
        failsafeTimers[timer_index] = datetime.now()


# def add_waypoint(location_link_coordinates):
#     right_click(location_link_coordinates)
#     time.sleep(0.5)
#     left_click(ui_tree.find_node({'_name': 'context_menu_Set Destination'}))
#     customPrint("Waypoint added")
#
#
# def setDestination(x, y):
#     rightClick(x, y)
#     time.sleep(0.5)
#     leftClick(x + 46, y + 56)
#     customPrint("Destination added")


def close_client(player_name):
    log_console("Closing client")
    eve = win32gui.FindWindow(None, fr"EVE - {player_name}")
    if eve != 0:
        win32gui.PostMessage(eve, win32con.WM_CLOSE, 0, 0)
    else:
        eve = win32gui.FindWindow("trinityWindow", "EVE")
        if eve != 0:
            win32gui.PostMessage(eve, win32con.WM_CLOSE, 0, 0)


def start_game(player_name):
    log_console("Starting client")
    start_failsafe()
    btn_play_now = pyautogui.locateOnScreen("images/btn_play_now.png", grayscale=True, confidence=0.7)
    while not btn_play_now:
        time.sleep(5)
        btn_play_now = pyautogui.locateOnScreen("images/btn_complete_mission.png", grayscale=True, confidence=0.7)
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
    while win32gui.FindWindow(None, fr"EVE - {player_name}") == 0:
        win32gui.SetForegroundWindow(eve)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(9)
        failsafe(60)
    ui_tree = UITree(CHARACTER_NAME)
    while not ui_tree.find_node({'_name': 'EVEMenuIcon'}):
        log_console(f"Waiting for neo-com {trial_count}")
        trial_count += 1
        if trial_count > 10:
            raise Exception("Can't find neo-com")
        time.sleep(5)
    time.sleep(5)
    start_img = pyautogui.screenshot()
    start_img.save(fr"startImg{fatalErrorCount}.png")
    time.sleep(5)
