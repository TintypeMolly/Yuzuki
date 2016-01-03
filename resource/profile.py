# -*- coding: utf-8 -*-
import re

from twisted.web.http import BAD_REQUEST

from exception import Unauthorized, BadRequest
from helper.content import markdown_and_linkify
from helper.pbkdf2 import pbkdf2
from helper.resource import YuzukiResource, need_anybody_permission
from helper.template import render_template
from model.user import User


class Profile(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("view", ProfileView())
        self.putChild("edit", ProfileEdit())
        self.putChild("popup", ProfilePopup())


class ProfileView(YuzukiResource):
    def render_GET(self, request):
        if not request.user:
            raise Unauthorized()
        return render_template("profile_view.html", request)


class ProfileEdit(YuzukiResource):
    def render_GET(self, request):
        if not request.user:
            raise Unauthorized()
        return render_template("profile_edit.html", request)

    def render_POST(self, request):
        if not request.user:
            raise Unauthorized()
        nickname = request.get_argument("nickname") or None
        password = request.get_argument("password") or None
        pd_realname = request.get_argument("pd_realname") or None
        pd_email = request.get_argument("pd_email") or None
        pd_address = request.get_argument("pd_address") or None
        pd_phone = request.get_argument("pd_phone") or None
        pd_bio = request.get_argument("pd_bio") or None

        # error check
        err = None
        if nickname:
            query = request.dbsession.query(User)\
                                     .filter(User.nickname == nickname)
            if request.dbsession.query(query.exists()).scalar():
                err = u"이미 사용되고 있는 별명입니다."
            elif not re.match(u"^[-_a-zA-Z가-힣\\d\\(\\)]{1,}$", nickname):
                err = u"별명은 영문, 한글, 숫자, 붙임표(-), 밑줄(_)과 괄호만 사용할 수 있습니다."

        if err:
            context = {"err": err}
            request.setResponseCode(BAD_REQUEST)
            return render_template("profile_edit.html", request, context)

        if nickname:
            request.user.nickname = nickname
        if password:
            request.user.password = pbkdf2(password)
        if pd_realname:
            request.user.pd_realname = pd_realname
        if pd_email:
            request.user.pd_email = pd_email
        if pd_address:
            request.user.pd_address = pd_address
        if pd_phone:
            request.user.pd_phone = pd_phone
        if pd_bio:
            request.user.pd_bio = markdown_and_linkify(pd_bio)

        request.dbsession.commit()
        request.redirect("/profile/view")
        return "profile edit success"


class ProfilePopup(YuzukiResource):
    @need_anybody_permission
    def render_GET(self, request):
        user_id = request.get_argument("user_id")
        query = request.dbsession.query(User).filter(User.uid == user_id)
        result = query.all()
        if not result:
            raise BadRequest()
        user = result[0]
        context = {"user": user}
        return render_template("profile_popup.html", request, context)
