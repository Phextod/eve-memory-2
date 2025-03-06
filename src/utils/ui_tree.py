import ctypes
import json
import time

import pyautogui
import pyscreeze
import win32gui

from src import config
from src.utils.singleton import Singleton

pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False


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

    def find_image(self, img_file_path, region_size_offset=50, confidence=0.9):
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


@Singleton
class UITree(object):

    def __init__(self):
        self.hwnd = win32gui.FindWindow(None, f"EVE - {config.CHARACTER_NAME}")
        self.window_position_offset = (0, 0)
        self.nodes: dict[int, UITreeNode] = dict()
        # self.width_ratio = 0
        # self.height_ratio = 0

        self.eve_memory_reader = ctypes.WinDLL(config.MEMORY_READER_DLL_PATH)
        self.eve_memory_reader.initialize.argtypes = []
        self.eve_memory_reader.initialize.restype = ctypes.c_int
        self.eve_memory_reader.read_ui_trees.argtypes = []
        self.eve_memory_reader.read_ui_trees.restype = None
        self.eve_memory_reader.get_ui_json.argtypes = []
        self.eve_memory_reader.get_ui_json.restype = ctypes.c_char_p
        self.eve_memory_reader.free_ui_json.argtypes = []
        self.eve_memory_reader.free_ui_json.restype = None
        self.eve_memory_reader.cleanup.argtypes = []
        self.eve_memory_reader.cleanup.restype = None

        ret = self.eve_memory_reader.initialize()
        if ret != 0:
            raise Exception(f"Failed to initialize: {ret}")
        self.refresh()

    def cleanup(self):
        self.eve_memory_reader.cleanup()

    def ingest(self, tree, x=0, y=0, parent=None):
        node = UITreeNode(**{**tree, **dict(
            x=x + self.window_position_offset[0] + config.HORIZONTAL_OFFSET,
            y=y + self.window_position_offset[1] + config.WINDOW_HEADER_OFFSET,
            parent=parent
        )})
        self.nodes[node.address] = node
        for child in tree.get("children", list()):
            real_x = x + (child["attrs"].get("_displayX", 0) or 0)
            real_y = y + (child["attrs"].get("_displayY", 0) or 0)
            self.ingest(child, real_x, real_y, tree["address"])

    def del_subtree_nodes(self, root_address):
        subtree_nodes = self.get_sub_tree_nodes(root_address)

        parent_address = self.nodes[root_address].parent
        self.nodes[parent_address].children.remove(root_address)

        for node_address in subtree_nodes:
            del self.nodes[node_address]

    def load(self, tree, root_address=None):
        parent = None
        real_x = 0
        real_y = 0

        if root_address:
            parent = self.nodes[root_address].parent
            self.del_subtree_nodes(root_address)
            self.nodes[parent].children.append(root_address)
            real_x = self.nodes[parent].x \
                + (tree["attrs"].get("_displayX", 0) or 0) \
                - self.window_position_offset[0] \
                - config.HORIZONTAL_OFFSET
            real_y = self.nodes[parent].y \
                + (tree["attrs"].get("_displayY", 0) or 0) \
                - self.window_position_offset[1] \
                - config.WINDOW_HEADER_OFFSET
        else:
            self.nodes = dict()

        self.ingest(tree, parent=parent, x=real_x, y=real_y)

        # if self.width_ratio == 0 or self.height_ratio == 0:
        #     screensize = get_screensize()
        #     self.width_ratio = screensize[0] / tree["attrs"].get("_displayWidth")
        #     self.height_ratio = screensize[1] / tree["attrs"].get("_displayHeight")

        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.window_position_offset = (window_rect[0], window_rect[1])

    def refresh(self, root_address=None):
        while True:
            if root_address:
                if not self.nodes.get(root_address):
                    return False
                else:
                    self.eve_memory_reader.read_ui_trees_from_address(ctypes.c_ulonglong(root_address))
            else:
                self.eve_memory_reader.read_ui_trees()
            tree_bytes = self.eve_memory_reader.get_ui_json()
            self.eve_memory_reader.free_ui_json()
            if not tree_bytes:
                print("no ui trees found")
            try:
                tree_str = tree_bytes.decode("utf-8", errors="ignore")

                # with open("ui_tree.json", "w") as f:
                #     f.write(tree_str)

                tree = json.loads(tree_str)
                self.load(tree, root_address)
            except UnicodeDecodeError as e:
                print(f"error reading ui trees: {e}")
            except ValueError as e:
                print(f"error reading ui trees: {e}")

            return True

    def find_node(
            self,
            query=None,
            address=None,
            node_type=None,
            select_many=False,
            contains=False,
            root: UITreeNode = None,
            refresh=True
    ):
        if query is None:
            query = {}

        if refresh:
            if root:
                if not self.refresh(root.address):
                    return None
                root = self.nodes.get(root.address)
            else:
                self.refresh()

        nodes = []

        candidates = self.get_sub_tree_nodes(root.address).items() if root \
            else self.nodes.items()

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

        if not select_many:
            if nodes:
                return nodes[0]
            return None
        return nodes

    def get_sub_tree_nodes(self, root_address, node_list: dict[int, UITreeNode] = None):
        if node_list is None:
            node_list = dict()

        root_node = self.nodes.get(root_address)

        if not root_node:
            return node_list

        for child_address in root_node.children:
            self.get_sub_tree_nodes(child_address, node_list)

        node_list.update({root_address: root_node})
        return node_list
