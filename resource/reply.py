# -*- coding: utf-8 -*-
import json

from twisted.web.http import NOT_FOUND, UNAUTHORIZED

from sqlalchemy.orm import subqueryload
from exception import BadArgument

from helper.resource import YuzukiResource
from model.article import Article
from model.reply import Reply


class ReplyParent(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("view", ReplyView())
        self.putChild("write", ReplyWrite())
        self.putChild("delete", ReplyDelete())


class ReplyView(YuzukiResource):
    REPLY_PER_PAGE = 15

    def render_GET(self, request):
        article_id = request.get_argument("article_id")
        try:
            page = int(request.get_argument("page", "1"))
        except ValueError:
            raise BadArgument("page", request.get_argument("page"))
        query = request.dbsession.query(Article) \
            .filter(Article.uid == article_id) \
            .filter(Article.enabled == True) \
            .options(subqueryload(Article.board))
        result = query.all()
        if not result:
            request.setResponseCode(NOT_FOUND)
            return "article not found"
        article = result[0]
        if article.board.name == "notice" or (
                    request.user and any([group.name == "anybody" for group in request.user])):
            query = request.dbsession.query(Reply) \
                .filter(Reply.article == article) \
                .filter(Reply.enabled == True) \
                .order_by(Reply.uid.desc()) \
                .options(subqueryload(Reply.user))
            start_idx = self.REPLY_PER_PAGE * (page - 1)
            end_idx = start_idx + self.REPLY_PER_PAGE - 1
            result = query[start_idx:end_idx]
            return json.dumps([reply.to_dict() for reply in result])
        else:
            request.setResponseCode(UNAUTHORIZED)
            return "unauthorized"


class ReplyWrite(YuzukiResource):
    def render_POST(self, request):
        pass


class ReplyDelete(YuzukiResource):
    def render_DELETE(self, request):
        pass