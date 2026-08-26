import sys
import threading
import time

import keyboard
import win32gui
from PyQt6.QtCore import QRect, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QApplication, QMainWindow
from screeninfo import get_monitors

from src.utils.ui_tree import UITreeNode, UITree


# 1. Create a Signal Bridge to safely communicate between threads
class SignalBridge(QObject):
    clear_signal = pyqtSignal()
    add_rect_signal = pyqtSignal(int, int, int, int)
    close_signal = pyqtSignal()


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

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Allows clicking through the transparent window to interact with the game/app behind it
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

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
        self.rectangles.clear()
        self._add_frame_rectangle()
        self.update()

    def add_rectangle(self, x, y, width, height):
        self.rectangles.append(QRect(x + self.pen_size // 2,
                                     y + self.pen_size // 2,
                                     width - self.pen_size * 2,
                                     height - self.pen_size * 2))
        self.update()


def dfs(ui_tree: UITree, parent_node: UITreeNode, _cursor_loc: tuple, bridge: SignalBridge, depth=0):
    for children_index in parent_node.children:
        children_node = ui_tree.nodes[children_index]
        width = children_node.attrs.get("_displayWidth", 0)
        height = children_node.attrs.get("_displayHeight", 0)

        if width and height:
            if (children_node.x <= _cursor_loc[0] <= children_node.x + width
                    and children_node.y <= _cursor_loc[1] <= children_node.y + height):
                print(depth * " " + str(children_index) + ": " + children_node.type + str(children_node.attrs))

                # Emit signal instead of directly calling the window method
                bridge.add_rect_signal.emit(
                    children_node.x,
                    children_node.y,
                    width,
                    height
                )

        dfs(ui_tree, children_node, _cursor_loc, bridge, depth=depth + 1)


# 2. This is your background logic running in a separate thread
def keyboard_listener(ui_tree: UITree, bridge: SignalBridge):
    ui_tree.refresh()

    while True:
        try:
            # Using is_pressed is safer in loops than read_key()
            if keyboard.is_pressed("enter"):
                print("----------------------")
                bridge.clear_signal.emit()  # Safely tell GUI to clear
                cursor_loc = win32gui.GetCursorPos()

                root = next(iter(ui_tree.nodes.values()))
                dfs(ui_tree, root, cursor_loc, bridge)

                time.sleep(0.3)  # Debounce to prevent multiple triggers from a single press

            elif keyboard.is_pressed("r"):
                print("----------------------")
                print("refresh")
                ui_tree.refresh()
                time.sleep(0.3)  # Debounce

            elif keyboard.is_pressed("esc"):
                bridge.close_signal.emit()  # Safely tell GUI to close
                break

        except Exception as e:
            print(f"Error in keyboard listener: {e}")

        time.sleep(0.01)  # Prevent the loop from maxing out CPU core


def main():
    # 3. GUI initializes and runs on the MAIN thread
    app = QApplication(sys.argv)
    window = RectangleWindow()

    # 4. Set up the signal bridge
    bridge = SignalBridge()
    bridge.clear_signal.connect(window.clear_rectangles)
    bridge.add_rect_signal.connect(window.add_rectangle)
    bridge.close_signal.connect(window.close)

    # 5. Start the background logic thread, passing it the bridge
    listener_thread = threading.Thread(target=keyboard_listener, args=(bridge,), daemon=True)
    listener_thread.start()

    # 6. Start the blocking GUI event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()