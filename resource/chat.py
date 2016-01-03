# -*- coding: utf-8 -*-
import json
from datetime import datetime

from twisted.internet import reactor
from twisted.web.http import BAD_REQUEST
from twisted.web.server import NOT_DONE_YET

from config.config import CHAT_PER_PAGE, CHAT_CONNECTION_INTERVAL
from exception import BadRequest
from helper.chat_cmd import ChatCmdManager
from helper.model_control import get_chat_newer_than, get_chat_page,\
    create_chat
from helper.resource import YuzukiResource, need_anybody_permission
from helper.template import render_template
from model.chat import Chat as ChatModel
from model.user import User as UserModel


def yuzuki_convert_int(num_str):
    try:
        value = int(num_str)
        return value
    except ValueError:
        raise BadRequest()


class Chat(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("user", ChatUser())
        self.putChild("message", ChatMessage())

    @need_anybody_permission
    def render_GET(self, request):
        page = request.get_argument("page", None)
        chat_total_count = request.dbsession.query(ChatModel).count()
        page_total = chat_total_count / CHAT_PER_PAGE
        user_nicknames = request.dbsession.query(UserModel.nickname).all()
        plucked_user_nicknames = [nickname for (nickname, ) in user_nicknames]

        if page_total % CHAT_PER_PAGE != 0:
            page_total += 1
        context = {
            "CHAT_PER_PAGE": CHAT_PER_PAGE,
            "page": page,
            "page_total": page_total,
            "user_nicknames": json.dumps(plucked_user_nicknames)
        }
        return render_template("chat.html", request, context)


class ChatUser(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        stream = ChatUserStream()
        self.putChild("data", ChatUserData(stream))
        self.putChild("out", ChatUserOut(stream))
        self.putChild("stream", stream)


class ChatMessage(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("data", ChatMessageData())
        self.putChild("stream", ChatMessageStream())


class ChatMessageStream(YuzukiResource):
    def __init__(self):
        YuzukiResource.__init__(self)
        self.request_pool = list()
        self.cmd_manager = ChatCmdManager()

    @need_anybody_permission
    def render_GET(self, request):
        self.request_pool.append(request)
        return NOT_DONE_YET

    @need_anybody_permission
    def render_POST(self, request):
        content = request.get_argument("content")
        if content.startswith("/"):
            chat, err = self.cmd_manager.process_cmd(request, content)
            if err:
                request.setResponseCode(BAD_REQUEST)
                return err
        else:
            chat = create_chat(request, content)
        request.dbsession.add(chat)
        request.dbsession.commit()
        for req in self.request_pool:
            try:
                req.write("message coming")
                req.finish()
            except:
                pass
        self.request_pool = []
        return "chat posted"


class ChatMessageData(YuzukiResource):
    @need_anybody_permission
    def render_GET(self, request):
        chat_id = request.get_argument("id", None)
        page = request.get_argument("page", None)
        if not chat_id and not page:
            raise BadRequest()
        if chat_id:
            chat_id = yuzuki_convert_int(chat_id)
            chats = get_chat_newer_than(request, chat_id)
        else:
            page = yuzuki_convert_int(page)
            chats = get_chat_page(request, page)
        data = [chat.to_dict() for chat in chats]
        data = sorted(data, key=lambda c: c["uid"])
        request.setNoCache()
        return json.dumps(data)


class ChatUserStream(YuzukiResource):
    def __init__(self):
        YuzukiResource.__init__(self)
        self.request_pool = list()
        self.user_pool = dict()

    def notify_all(self):
        for req in self.request_pool:
            if not req.finished:
                req.write("refresh")
                req.finish()
        self.request_pool = list()

    def send_refresh_signal(self, request):
        if request in self.request_pool:
            self.request_pool.remove(request)
        if not request.finished:
            request.write("refresh")
            request.finish()

    def response_failed(self, err, request, call):
        call.cancel()
        if request in self.request_pool:
            self.request_pool.remove(request)
        self.notify_all()

    @need_anybody_permission
    def render_GET(self, request):
        self.request_pool.append(request)
        call = reactor.callLater(CHAT_CONNECTION_INTERVAL - 5,
                                 self.send_refresh_signal, request)
        request.notifyFinish().addErrback(self.response_failed, request, call)
        refresh_flag = False
        if request.user not in self.user_pool:
            refresh_flag = True
        self.user_pool[request.user] = datetime.now()
        new_user_pool = dict()
        for user, connection_time in self.user_pool.iteritems():
            if (datetime.now() - connection_time).seconds <= \
               CHAT_CONNECTION_INTERVAL:
                new_user_pool[user] = connection_time
            else:
                refresh_flag = True
        self.user_pool = new_user_pool
        if refresh_flag:
            self.request_pool.remove(request)
            self.notify_all()
            return "refresh"
        else:
            return NOT_DONE_YET


class ChatUserData(YuzukiResource):
    def __init__(self, stream):
        YuzukiResource.__init__(self)
        self.stream = stream

    @need_anybody_permission
    def render_GET(self, request):
        user_data_list = list()
        for user in self.stream.user_pool:
            user_data = {
                "user_id": user.uid,
                "user_nickname": user.nickname,
            }
            user_data_list.append(user_data)
        user_data_list = sorted(user_data_list, key=lambda u: u["user_id"])
        request.setNoCache()
        return json.dumps(user_data_list)


class ChatUserOut(YuzukiResource):
    def __init__(self, stream):
        YuzukiResource.__init__(self)
        self.stream = stream

    @need_anybody_permission
    def render_GET(self, request):
        if request.user in self.stream.user_pool:
            del (self.stream.user_pool[request.user])
            self.stream.notify_all()
        return "out"
