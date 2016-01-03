# -*- coding: utf-8 -*-
import re

from twisted.web.http import BAD_REQUEST

from helper.database import DatabaseHelper
from helper.resource import YuzukiResource
from helper.template import render_template
from model.group import Group
from model.user import User


class Register(YuzukiResource):
    def __init__(self):
        YuzukiResource.__init__(self)
        dbsession = DatabaseHelper.session()
        query = dbsession.query(Group).filter(Group.important)
        result = query.all()
        self.bunryu_groups = [(group.uid, group.name) for group in result]
        dbsession.close()

    def render_GET(self, request):
        context = {"group_meta": self.bunryu_groups}
        return render_template("register.html", request, context)

    def render_POST(self, request):
        username = request.get_argument("username") or None
        nickname = request.get_argument("nickname") or None
        password = request.get_argument("password") or None
        pd_realname = request.get_argument("pd_realname") or None
        pd_email = request.get_argument("pd_email") or None
        pd_address = request.get_argument("pd_address") or None
        pd_phone = request.get_argument("pd_phone") or None
        pd_bunryu = request.get_argument("pd_bunryu") or None
        pd_bio = request.get_argument("pd_bio") or None
        new_user = User(username, nickname, password, pd_realname,
                        pd_email, pd_address, pd_phone, pd_bunryu, pd_bio)
        err = self.check_user_data_valid(request, new_user)
        if not err:
            request.dbsession.add(new_user)
            request.dbsession.commit()
            request.redirect("/welcome")
            return "registered successfully"
        else:
            request.setResponseCode(BAD_REQUEST)
            context = {
                "group_meta": self.bunryu_groups,
                "err": err,
            }
            return render_template("register.html", request, context)

    def check_user_data_valid(self, request, new_user):
        # empty value check
        if not new_user.username:
            return u"ID는 비어있을 수 없습니다."
        if not new_user.nickname:
            return u"별명은 비어있을 수 없습니다."
        if not new_user.password:
            return u"비밀번호는 비어있을 수 없습니다."
        if not new_user.pd_realname:
            return u"실명은 비어있을 수 없습니다."
        if not new_user.pd_bunryu:
            return u"분류는 비어있을 수 없습니다."

        # nickname username regex validity check
        if not re.match(u"^[-_a-zA-Z가-힣\\d\\(\\)]{1,}$", new_user.username):
            return u"ID는 영문, 한글, 숫자, 붙임표(-), 밑줄(_)과 괄호만 사용할 수 있습니다."
        if not re.match(u"^[-_a-zA-Z가-힣\\d\\(\\)]{1,}$", new_user.nickname):
            return u"별명은 영문, 한글, 숫자, 붙임표(-), 밑줄(_)과 괄호만 사용할 수 있습니다."

        # duplicate value check
        user_query = request.dbsession.query(User)
        query = user_query.filter(User.username == new_user.username)
        if request.dbsession.query(query.exists()).scalar():
            return u"이미 사용되고 있는 ID입니다."
        query = user_query.filter(User.nickname == new_user.nickname)
        if request.dbsession.query(query.exists()).scalar():
            return u"이미 사용되고 있는 별명입니다."

        # bunryu existence check
        query = request.dbsession.query(Group)\
                                 .filter(Group.uid == new_user.pd_bunryu)
        result = query.all()
        if not result:
            return u"존재하지 않는 분류 그룹입니다."
        else:
            group = result[0]
            group.users.append(new_user)

        # all green
        return None
