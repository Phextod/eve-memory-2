import ctypes
import json
import time

import pyautogui
import win32gui

import pyscreeze
pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False

eve_memory_reader = ctypes.WinDLL(r"D:\Projects\Python\eve-memory-2\src\utils\eve-memory-reader.dll")
# eve_memory_reader = ctypes.WinDLL(r"D:\Projects\Python\eve-memory-2\eve-memory-reader(old).dll")

eve_memory_reader.initialize.argtypes = []
eve_memory_reader.initialize.restype = ctypes.c_int
eve_memory_reader.read_ui_trees.argtypes = []
eve_memory_reader.read_ui_trees.restype = None
eve_memory_reader.get_ui_json.argtypes = []
eve_memory_reader.get_ui_json.restype = ctypes.c_char_p
eve_memory_reader.free_ui_json.argtypes = []
eve_memory_reader.free_ui_json.restype = None
eve_memory_reader.cleanup.argtypes = []
eve_memory_reader.cleanup.restype = None

WINDOW_HEADER_OFFSET = 32
HORIZONTAL_OFFSET = 10  # don't know where it comes from


def get_screensize():
    return ctypes.windll.user32.GetSystemMetrics(
        0
    ), ctypes.windll.user32.GetSystemMetrics(1)


class UITreeNode(object):
    def __init__(self, **node):
        self.address: int = node.get("address")
        self.type: str = node.get("type")
        self.attrs = node.get("attrs", dict())
        self.x: int = node.get("x", 0)
        self.y: int = node.get("y", 0)
        self.parent: int = node.get("parent")
        self.data = dict()  # arbitrary data
        self.children: list[int] = list()
        for child in node.get("children", list()):
            self.children.append(child.get("address"))

    def get_center(self, pos_x=0.5, pos_y=0.5):
        width = self.attrs.get("_displayWidth", 20) or 20
        height = self.attrs.get("_displayHeight", 20) or 20
        x = self.x + round(width * pos_x)
        y = self.y + round(height * pos_y)
        return x, y

    def get_region(self, add_size=0):
        left = self.x - add_size
        top = self.y - add_size
        width = self.attrs.get("_displayWidth") + add_size * 2
        height = self.attrs.get("_displayHeight") + add_size * 2
        return left, top, width, height

    def find_image(self, img_file_path, region_size_offset=30, confidence=0.9):
        img = None

        error_counter = 0
        while True:
            try:
                img = pyautogui.locateOnScreen(
                    img_file_path,
                    region=self.get_region(region_size_offset),
                    grayscale=True,
                    confidence=confidence
                )
            except ValueError as ve:
                # if img is larger than region
                if error_counter >= 5:
                    raise ve
                error_counter += 1

                time.sleep(1)
                continue
            break

        if not img:
            return None

        new_node = UITreeNode()
        new_node.x = img.left.item()
        new_node.y = img.top.item()
        new_node.attrs.update({"_displayWidth": img.width})
        new_node.attrs.update({"_displayHeight": img.height})

        return new_node


class UITree(object):
    def __init__(self, character_name):
        self.character_name = character_name
        self.window_position_offset = (0, 0)
        self.nodes: dict[int, UITreeNode] = dict()
        self.width_ratio = 0
        self.height_ratio = 0
        ret = eve_memory_reader.initialize()
        if ret != 0:
            raise Exception(f"Failed to initialize: {ret}")
        self.refresh()

    @staticmethod
    def cleanup():
        eve_memory_reader.cleanup()

    def ingest(self, tree, x=0, y=0, parent=None):
        node = UITreeNode(**{**tree, **dict(
            x=x + self.window_position_offset[0] + HORIZONTAL_OFFSET,
            y=y + self.window_position_offset[1] + WINDOW_HEADER_OFFSET,
            parent=parent
        )})
        self.nodes[node.address] = node
        for child in tree.get("children", list()):
            real_x = x + (child["attrs"].get("_displayX", 0) or 0)
            real_y = y + (child["attrs"].get("_displayY", 0) or 0)
            self.ingest(child, real_x, real_y, tree["address"])

    def load(self, tree):
        self.nodes = dict()
        self.ingest(tree)
        try:
            if (
                    tree["attrs"].get("_displayWidth", 0) is None
                    or tree["attrs"].get("_displayHeight", 0) is None
            ):
                raise ZeroDivisionError
            screensize = get_screensize()
            self.width_ratio = screensize[0] / tree["attrs"].get("_displayWidth", 0)
            self.height_ratio = screensize[1] / tree["attrs"].get("_displayHeight", 0)
        except ZeroDivisionError:
            self.refresh()

    def refresh(self):
        window_name = f"EVE - {self.character_name}"
        hwnd = win32gui.FindWindow(None, window_name)
        window_rect = win32gui.GetWindowRect(hwnd)
        self.window_position_offset = (window_rect[0], window_rect[1])

        eve_memory_reader.read_ui_trees()
        tree_bytes = eve_memory_reader.get_ui_json()
        eve_memory_reader.free_ui_json()
        if not tree_bytes:
            print("no ui trees found")
            return
        try:
            tree_str = tree_bytes.decode("utf-8", errors="ignore")
            tree = json.loads(tree_str)
            self.load(tree)
        except UnicodeDecodeError as e:
            print(f"error reading ui trees: {e}")
            return
        except ValueError as e:
            print(f"error reading ui trees: {e}")
            return

    def find_node(
            self,
            query=None,
            address=None,
            node_type=None,
            select_many=False,
            contains=False,
            root: UITreeNode = None,
            refresh=False
    ):
        if query is None:
            query = {}

        if refresh:
            self.refresh()

        nodes = list()

        candidates = self.nodes.items() \
            if root is None \
            else self.get_sub_tree_nodes(root).items()

        for _, node in candidates:
            if address and node.address != address:
                continue
            if node_type and node.type != node_type:
                continue
            if all([
                node.attrs.get(q_key) == q_val
                if not contains
                else q_val in str(node.attrs.get(q_key, ""))
                for q_key, q_val in query.items()
            ]):
                nodes.append(node)
                if not select_many:
                    break

        if nodes and not select_many:
            return nodes[0]
        return nodes

    def get_sub_tree_nodes(self, root: UITreeNode, node_list: dict[int, UITreeNode] = None):
        if node_list is None:
            node_list = dict()

        for child_id in root.children:
            child_node = self.nodes.get(child_id)
            self.get_sub_tree_nodes(child_node, node_list)

        node_list.update({root.address: root})
        return node_list
