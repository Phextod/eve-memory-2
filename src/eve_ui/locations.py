import time
from typing import TYPE_CHECKING

from src.utils.bubbling_query import BubblingQuery
from src.utils.utils import click

if TYPE_CHECKING:
    # Only imported during static type checking, ignored at runtime
    from src.eve_ui.eve_ui import EveUI


class Locations:
    def __init__(self, eve_ui: 'EveUI', refresh_on_init=False, do_setup=True):
        self.eve_ui: EveUI = eve_ui

        self.main_window_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="LocationsWindow",
            refresh_on_init=refresh_on_init,
        )
        self.main_container_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            query={'_name': 'maincontainer'},
            parent_query=self.main_window_query,
            refresh_on_init=False,
        )

        should_close_groups = do_setup and self.eve_ui.ui_tree.find_node(
            {'texturePath': 'res:/UI/Texture/Icons/38_16_229.png'},
            root=self.main_container_query.result,
            refresh=False,
        ) is not None
        if should_close_groups:
            self.close_groups(refresh_on_init)

    def close_groups(self, refresh=True):
        btn_close = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            query={'_name': 'collapseCont'},
            parent_query=self.main_window_query,
            refresh_on_init=refresh
        ).result
        click(btn_close)

    def get_group(self, node_type, name):
        groups = self.eve_ui.ui_tree.find_node(
            node_type=node_type,
            select_many=True,
            root=self.main_container_query.result,
        )

        for group in groups:
            label = self.eve_ui.ui_tree.find_node(node_type="EveLabelMedium", root=group, refresh=False)

            label_text = label.attrs['_setText'].split("<")[0].strip()
            if label_text == name:
                return group

        return None

    def _expand_if_not_expanded(self, root):
        expander = self.eve_ui.ui_tree.find_node({'_name': 'expander'}, root=root, refresh=False)
        if expander.attrs["texturePath"] != "res:/UI/Texture/Icons/38_16_229.png":
            click(expander)
            time.sleep(0.1)

    def get_entry(self, path_str):
        """
        :param path_str: Path in the folder structure. Example: "Personal Locations/Abyss/safe spot"
        """
        self.main_container_query.run()
        path = path_str.split("/")
        path_index = 0

        if len(path) > 1:
            if not (entry := self.get_group("ListGroup", path[path_index])):
                return None
            self._expand_if_not_expanded(entry)
            path_index += 1

        if len(path) > 2:
            if not (entry := self.get_group("BookmarkFolderGroup", path[path_index])):
                return None
            self._expand_if_not_expanded(entry)
            path_index += 1

        if len(path) > 3:
            if not (entry := self.get_group("BaseFolderGroup", path[path_index])):
                return None
            self._expand_if_not_expanded(entry)
            path_index += 1

        return self.get_group("PlaceEntry", path[path_index])
