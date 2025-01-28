import time

import win32gui
import win32process

from src.utils.interface import UITree
from src.utils.utils import CHARACTER_NAME

window_name = f"EVE - {CHARACTER_NAME}"
hwnd = win32gui.FindWindow(None, window_name)
_, pid = win32process.GetWindowThreadProcessId(hwnd)

ui_tree = UITree(CHARACTER_NAME)

REPEAT_NUMBER = 30

start_time = time.time()
for _ in range(REPEAT_NUMBER):
    ui_tree.refresh()
print((time.time() - start_time) / REPEAT_NUMBER)

root_node = ui_tree.find_node({'_name': 'markersParent'})

start_time = time.time()
for _ in range(REPEAT_NUMBER):
    ui_tree.refresh_subtree(root_node.address)
print((time.time() - start_time) / REPEAT_NUMBER)
