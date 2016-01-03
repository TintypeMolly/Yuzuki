# -*- coding: utf-8 -*-
# flake8: noqa
from hashlib import sha256

from helper.database import DatabaseHelper
from model.board import Board
from model.group import Group
from model.user import User

DatabaseHelper.create_all()
dbsession = DatabaseHelper.session()

"""
BASIC REQUIREMENT FROM HERE
"""
anybody = Group(u"anybody")
anybody.description = "All user must be approved by being assigned to this group"
dbsession.add(anybody)

nobody = Group("nobody")
nobody.description = "nobody can be registered in this group"
dbsession.add(nobody)

admin = Group("admin")
dbsession.add(admin)

notice = Board("notice", u"공지사항", admin, anybody)
dbsession.add(notice)

free = Board("free", u"자유게시판", anybody, anybody)
dbsession.add(free)

dbsession.commit()

"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!                                                                                                 !!!
!!!                                         VERY IMPORTANT                                          !!!
!!!                                CHANGE ADMIN PASSWORD BEFORE INSTALL                             !!!
!!!                                                                                                 !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""
admin_user = User("admin", u"webmaster", sha256("asdf1234").hexdigest(), u"웹마스터", None, None, None, admin.uid, None)
admin_user.is_admin = True
admin.users.append(admin_user)
anybody.users.append(admin_user)
dbsession.add(admin_user)

chat_user = User("chat_system", "system", "asdf", "system", None, None, None, admin.uid, None)
chat_user.password = ""
anybody.users.append(chat_user)
dbsession.add(chat_user)

dbsession.commit()
"""
BASIC REQUIREMENT TO HERE
"""

"""
FOR POOLC FROM HERE
"""
game_dev = Group(u"게임제작부")
dbsession.add(game_dev)

hakbeons = ["14", "13", "12", "11", "10", "09", "08", "07", "06", "05", "04", "03", "02", "01", "00", "99", "98"]
for i, hakbeon in enumerate(hakbeons):
    hakbeon_group = Group(hakbeon + u"학번")
    hakbeon_group.important = True
    dbsession.add(hakbeon_group)

    hakbeon_board = Board("y" + hakbeon, hakbeon + u"학번 게시판", hakbeon_group, anybody, "normal", i + 1)
    dbsession.add(hakbeon_board)

seminar_board = Board("seminar", u"학술부", anybody, anybody, "somoim", 1)
dbsession.add(seminar_board)

game_dev_board = Board("game_dev", u"게임제작부", game_dev, game_dev, "somoim", 2)
dbsession.add(game_dev_board)

dbsession.commit()

"""
FOR POOLC TO HERE
"""

# dummy end
dbsession.close()
