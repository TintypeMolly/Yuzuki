# -*- coding: utf-8 -*-
from helper.database import DatabaseHelper
from model.board import Board


class SideMenuElement(object):
    anybody_allowed = False

    def render(self, is_anybody):
        if not self.anybody_allowed and not is_anybody:
            return u""
        else:
            return self.to_element()

    def to_element(self):
        raise NotImplementedError()


class ParentMenuElement(SideMenuElement):
    def __init__(self, name, repr, children, anybody_allowed):
        self.repr = repr
        self.name = name
        self.children = children
        self.anybody_allowed = anybody_allowed

    def to_element(self):
        return u"""
        <li>
            <a data-toggle="collapse" data-target="#%(name)s">%(repr)s</a>
            <ul id="%(name)s" class="nav nav-collapse collapse">
                %(children)s
            </ul>
        </li>
        """ % {
            "name": self.name,
            "repr": self.repr,
            "children": self.children_list_elements(),
        }

    def children_list_elements(self):
        return u"".join([child.to_element() for child in self.children])


class BoardMenuElement(SideMenuElement):
    def __init__(self, name, anybody_allowed):
        dbsession = DatabaseHelper.session()
        query = dbsession.query(Board).filter(Board.name == name)
        self.board = query.one()
        self.anybody_allowed = anybody_allowed

    def to_element(self):
        return u"""
        <li id="%(name)s">
            <a href="/board?name=%(name)s">
               %(repr)s
            </a>
        </li>
        """ % {
            "name": self.board.name,
            "repr": self.board.repr,
        }


class LinkMenuElement(SideMenuElement):
    def __init__(self, name, path, repr, anybody_allowed):
        self.path = path
        self.name = path.split("/")[-1]
        self.repr = repr
        self.anybody_allowed = anybody_allowed

    def to_element(self):
        return u"""
        <li id="%(name)s">
            <a href="%(path)s">
                %(repr)s
            </a>
        </li>
        """ % {
            "name": self.name,
            "path": self.path,
            "repr": self.repr,
        }


class ArbitraryMenuElement(SideMenuElement):
    def __init__(self, content, anybody_allowed):
        self.anybody_allowed = anybody_allowed
        self.content = content

    def to_element(self):
        return self.content
