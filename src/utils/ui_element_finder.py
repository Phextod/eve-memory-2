import sys
import threading
import time
from typing import Optional

import keyboard
import win32gui
from PyQt5 import QtCore
from PyQt5.QtCore import QRect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from screeninfo import get_monitors

from src.utils.ui_tree import UITreeNode, UITree


class RectangleWindow(QMainWindow):
    def __init__(
            self,
            x: int = 0,
            y: int = 0,
            width: int = -1,
            height: int = -1,
            pen_color: str = "#e62727",
            pen_size: int = 2):
        super().__init__()
        self.x = x
        self.y = y
        self.pen_color = pen_color
        self.pen_size = pen_size
        self.rectangles = []

        if width == -1 or height == -1:
            monitors = get_monitors()
            self.window_width = monitors[0].width
            self.window_height = monitors[0].height

        self.init_ui()

    def init_ui(self):
        self.setGeometry(self.x, self.y, self.window_width + self.pen_size, self.window_height + self.pen_size)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self._add_frame_rectangle()
        self.show()

    def _add_frame_rectangle(self):
        self.add_rectangle(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        for rect in self.rectangles:
            painter.setPen(QPen(QColor(self.pen_color), self.pen_size))
            painter.drawRect(rect)

    def clear_rectangles(self):
        self.rectangles = []
        self._add_frame_rectangle()
        self.update()

    def add_rectangle(self, x, y, width, height):
        self.rectangles.append(QRect(x + self.pen_size // 2,
                                     y + self.pen_size // 2,
                                     width - self.pen_size * 2,
                                     height - self.pen_size * 2))
        self.update()


highlight_window: Optional[RectangleWindow] = None


def dfs(parent_node: UITreeNode, _cursor_loc: (int, int), depth=0):
    for children_index in parent_node.children:
        children_node = UITree.instance().nodes[children_index]
        width = children_node.attrs.get("_displayWidth", 0)
        height = children_node.attrs.get("_displayHeight", 0)
        if width and height:
            if (children_node.x <= _cursor_loc[0] <= children_node.x + width
                    and children_node.y <= _cursor_loc[1] <= children_node.y + height):
                print(depth * " " + str(children_index) + ": " + children_node.type + str(children_node.attrs))
                highlight_window.add_rectangle(
                    children_node.x,
                    children_node.y,
                    width,
                    height)

        dfs(children_node, _cursor_loc, depth=depth + 1)


def start_qt():
    global highlight_window
    qt_app = QApplication(sys.argv)
    highlight_window = RectangleWindow()
    highlight_window.show()
    qt_app.exec()


def start_qt_thread():
    _qt_thread = threading.Thread(target=start_qt, daemon=True)
    _qt_thread.start()
    return _qt_thread


if __name__ == "__main__":
    UITree.instance()
    UITree.instance().refresh()  # No idea why but without this the first positions are incorrect

    qt_thread = start_qt_thread()
    time.sleep(1)

    while True:
        if keyboard.read_key() == "enter":
            print("----------------------")
            highlight_window.clear_rectangles()
            cursor_loc = win32gui.GetCursorPos()
            cursor_local_location = (
                cursor_loc[0],
                cursor_loc[1]
            )

            root = next(iter(UITree.instance().nodes.values()))
            dfs(root, cursor_local_location)
        elif keyboard.read_key() == "r":
            print("----------------------")
            print("refresh")
            UITree.instance().refresh()
        elif keyboard.read_key() == "esc":
            highlight_window.close()
            qt_thread.join()
            break

# for _, node in tree.nodes.items():
#     height = node.attrs["_displayHeight"]
#     width = node.attrs["_displayWidth"]
#     if not height or not width or not node.x or not node.y:
#         print(node.type)
