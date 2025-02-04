from typing import List, Union, Optional

from src.utils.interface import UITree, UITreeNode


class BubblingQuery:

    def __init__(
            self,
            query: dict = None,
            parent_query: "BubblingQuery" = None,
            node_type: str = None,
            select_many: bool = False,
            contains: bool = False,
            refresh_on_init=True,
    ):
        self.query: dict = query
        self.node_type: str = node_type
        self.select_many: bool = select_many
        self.contains: bool = contains
        self.parent_query: "BubblingQuery" = parent_query

        self.result: Union[Optional[UITreeNode], List[UITreeNode]] = None

        self.run(refresh_on_init)

    def run(self, refresh=True):
        self.result = None

        # If parent.result is a list then it shouldn't be a parent in the first place
        root_node = None if not self.parent_query else self.parent_query.result

        self.result = UITree.instance().find_node(
            query=self.query,
            node_type=self.node_type,
            select_many=self.select_many,
            contains=self.contains,
            root=root_node,
            refresh=refresh,
        )

        if not self.result and self.parent_query:
            if self.parent_query.run():
                self.result = UITree.instance().find_node(
                    query=self.query,
                    node_type=self.node_type,
                    select_many=self.select_many,
                    contains=self.contains,
                    root=self.parent_query.result,
                    refresh=False,
                )

        return self.result
