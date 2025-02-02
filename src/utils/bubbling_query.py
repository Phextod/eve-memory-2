from src.utils.interface import UITree


class BubblingQuery:

    def __init__(
            self,
            query: dict = None,
            parent_query: "BubblingQuery" = None,
            node_type: str = None,
            select_many: bool = False,
            contains: bool = False,
            ui_tree: UITree = None,
    ):
        self.query: dict = query
        self.node_type: str = node_type
        self.select_many: bool = select_many
        self.contains: bool = contains
        self.parent_query: "BubblingQuery" = parent_query

        self.ui_tree: UITree = ui_tree
        if parent_query:
            self.ui_tree = parent_query.ui_tree

        self.result = None

        self.run()

    def run(self, refresh=True):
        self.result = None

        # If parent.result is a list then it shouldn't be a parent in the first place
        root_node = None if not self.parent_query else self.parent_query.result

        self.result = self.ui_tree.find_node(
            query=self.query,
            node_type=self.node_type,
            select_many=self.select_many,
            contains=self.contains,
            root=root_node,
            refresh=refresh,
        )

        if not self.result and self.parent_query:
            if self.parent_query.run():
                self.result = self.ui_tree.find_node(
                    query=self.query,
                    node_type=self.node_type,
                    select_many=self.select_many,
                    contains=self.contains,
                    root=self.parent_query.result,
                    refresh=False,
                )

        return self.result
