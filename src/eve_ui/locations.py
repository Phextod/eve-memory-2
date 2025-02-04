import time

from src.utils.bubbling_query import BubblingQuery
from src.utils.ui_tree import UITree
from src.utils.utils import click


class Locations:
    def __init__(self, refresh_on_init=False):
        self.main_window_query = BubblingQuery(
            node_type="LocationsWindow",
            refresh_on_init=refresh_on_init,
        )
        self.main_container_query = BubblingQuery(
            {'_name': 'maincontainer'},
            self.main_window_query,
            refresh_on_init=refresh_on_init,
        )

        self.close_groups(refresh_on_init)

    def close_groups(self, refresh=True):
        btn_close = BubblingQuery({'_name': 'collapseCont'}, self.main_window_query, refresh_on_init=refresh).result
        click(btn_close)

    def get_group(self, node_type, name):
        groups = UITree.instance().find_node(
            node_type=node_type,
            select_many=True,
            root=self.main_container_query.result,
        )

        for group in groups:
            label = UITree.instance().find_node(node_type="EveLabelMedium", root=group, refresh=False)

            label_text = label.attrs['_setText'].split("<")[0].strip()
            if label_text == name:
                return group

        return None

    @staticmethod
    def _expand_if_not_expanded(root):
        expander = UITree.instance().find_node({'_name': 'expander'}, root=root, refresh=False)
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
