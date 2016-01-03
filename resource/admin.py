# -*- coding: utf-8 -*-
from sqlalchemy.orm import subqueryload

from exception import BadRequest
from helper.model_control import get_not_anybody_user
from helper.resource import YuzukiResource, need_admin_permission
from helper.template import render_template
from model.board import Board
from model.group import Group
from model.user import User


class Admin(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("approve", UserApprove())
        self.putChild("board", BoardManagement())

    @need_admin_permission
    def render_GET(self, request):
        return render_template("admin.html", request)


class UserApprove(YuzukiResource):
    @need_admin_permission
    def render_GET(self, request):
        YuzukiResource.__init__(self)
        users = get_not_anybody_user(request)
        context = {"users": users}
        return render_template("admin_approve.html", request, context)

    @need_admin_permission
    def render_POST(self, request):
        user_id = request.get_argument_int("user_id")
        query = request.dbsession.query(User).filter(User.uid == user_id)
        result = query.all()
        if not result:
            raise BadRequest()
        user = result[0]
        query = request.dbsession.query(Group).filter(Group.name == "anybody")
        anybody = query.one()
        anybody.users.append(user)
        request.dbsession.commit()
        request.redirect("/admin/approve")
        return "redirect"


class BoardManagement(YuzukiResource):
    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("edit", BoardEdit())
        self.putChild("add", BoardAdd())

    @need_admin_permission
    def render_GET(self, request):
        boards = request.dbsession.query(Board)\
                                  .options(subqueryload(Board.write_group))\
                                  .options(subqueryload(Board.write_group))\
                                  .all()
        context = {"boards": boards}
        return render_template("admin_board.html", request, context)


class BoardEdit(YuzukiResource):
    @need_admin_permission
    def render_GET(self, request):
        board_id = request.get_argument_int("id")
        query = request.dbsession.query(Board).filter(Board.uid == board_id)
        result = query.all()
        if not result:
            raise BadRequest()
        board = result[0]
        groups = request.dbsession.query(Group).all()
        context = {
            "board": board,
            "groups": groups,
        }
        return render_template("admin_board_edit.html", request, context)

    @need_admin_permission
    def render_POST(self, request):
        board_id = request.get_argument_int("id")
        query = request.dbsession.query(Board).filter(Board.uid == board_id)
        result = query.all()
        if not result:
            raise BadRequest()
        board = result[0]

        name = request.get_argument("name")
        repr = request.get_argument("repr")
        repr_order = request.get_argument_int("repr_order", None)
        classification = request.get_argument("classification") or None
        description = request.get_argument("description") or None
        write_group_uid = request.get_argument_int("write_group_uid")
        comment_group_uid = request.get_argument_int("comment_group_uid")
        enabled = request.get_argument("enabled") == "True"

        board.name = name
        board.repr = repr
        board.repr_order = repr_order
        board.classification = classification
        board.description = description
        board.write_group_uid = write_group_uid
        board.comment_group_uid = comment_group_uid
        board.enabled = enabled

        request.dbsession.commit()
        request.redirect("/admin/board")
        return "redirected"


class BoardAdd(YuzukiResource):
    @need_admin_permission
    def render_GET(self, request):
        pass
