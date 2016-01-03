# -*- coding: utf-8 -*-
# flake8: noqa
from helper.side_menu import (
    ParentMenuElement,
    BoardMenuElement,
    LinkMenuElement,
    ArbitraryMenuElement,
)
from helper.database import DatabaseHelper
from model.board import Board

dbsession = DatabaseHelper.session()
board_query = dbsession.query(Board)\
                       .filter(Board.enabled)\
                       .order_by(Board.repr_order.asc())
somoim_board_elements = [BoardMenuElement(b.name, False)
                         for b in
                         board_query.filter(Board.classification == "somoim")]
normal_board_elements = [BoardMenuElement(b.name, False)
                         for b in
                         board_query.filter(Board.classification == "normal")]
somoim = ParentMenuElement("somoim", u"소모임", somoim_board_elements, False)
normal = ParentMenuElement("normal", u"일반 게시판", normal_board_elements, False)
improve_button = ArbitraryMenuElement(u"""
<li>
    <a href="https://github.com/PoolC/Yuzuki/issues" target="_blank">홈페이지 개선</a>
    <iframe class="fork-button pull-right"
            src="https://ghbtns.com/github-btn.html?user=PoolC&repo=Yuzuki&type=fork&count=true"
            frameborder="0" scrolling="0" width="80px" height="20px">
    </iframe>
</li>
""", True)
SIDE_MENU = [
    LinkMenuElement("about", "/page/about", u"소개", True),
    BoardMenuElement("notice", True),
    LinkMenuElement("new", "/new", u"새 글", False),
    BoardMenuElement("free", False),
    somoim,
    normal,
    LinkMenuElement("chat", "https://poolc.slack.com/", u"채팅방", False),
    improve_button,
]
