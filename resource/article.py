# -*- coding: utf-8 -*-
import re

from config.config import REPLY_PER_PAGE
from exception import BadRequest, Unauthorized
from helper.model_control import get_board, get_article, delete_article, \
    edit_article, create_article
from helper.permission import can_write, is_anybody, is_author, \
    is_author_or_admin
from helper.resource import YuzukiResource, need_anybody_permission
from helper.template import render_template
from helper.slack import post_message as post_message_to_slack

article_content_re = re.compile(r'&(#\d+|[a-z]+);')


def replaceArticleContentForEdit(article):
    '''
    For editing article content with codemirror,
    HTML entities in article should be re-encoded into HTML entity.
    '''
    article.content = re.sub(article_content_re, r'&#38;\1;', article.content)
    return article


class ArticleParent(YuzukiResource):
    isLeaf = False

    def __init__(self):
        YuzukiResource.__init__(self)
        self.putChild("view", ArticleView())
        self.putChild("write", ArticleWrite())
        self.putChild("delete", ArticleDelete())
        self.putChild("edit", ArticleEdit())


class ArticleView(YuzukiResource):
    def render_GET(self, request):
        article_id = request.get_argument("id")
        article = get_article(request, article_id)
        page = request.get_argument("page", None)
        if article.board.name == "notice" or is_anybody(request):
            reply_page_total = article.reply_count / REPLY_PER_PAGE
            if article.reply_count % REPLY_PER_PAGE != 0:
                reply_page_total += 1
            context = {
                "article": article,
                "page": page,
                "reply_page_total": reply_page_total,
            }
            return render_template("article_view.html", request, context)
        else:
            raise Unauthorized()


class ArticleWrite(YuzukiResource):
    @need_anybody_permission
    def render_GET(self, request):
        board_name = request.get_argument("name")
        board = get_board(request, board_name)
        if not can_write(request, board):
            raise Unauthorized()
        context = {"board": board}
        return render_template("article_write.html", request, context)

    @need_anybody_permission
    def render_POST(self, request):
        board_name = request.get_argument("name")
        board = get_board(request, board_name)
        if not can_write(request, board):
            raise Unauthorized()
        subject = request.get_argument("subject")
        content = request.get_argument("content")
        # no empty subject
        if subject.strip():
            article = create_article(request, board, subject, content)
            request.dbsession.add(article)
            request.dbsession.commit()
            article_view_url = "/article/view?id=%s" % article.uid
            request.redirect(article_view_url)

            post_message_to_slack(request, article, article_view_url)
            return "article posted"
        else:
            raise BadRequest()


class ArticleDelete(YuzukiResource):
    @need_anybody_permission
    def render_DELETE(self, request):
        article_id = request.get_argument("id")
        article = get_article(request, article_id)
        if is_author_or_admin(request, article):
            delete_article(request, article)
            request.dbsession.commit()
            return "delete success"
        else:
            raise Unauthorized()


class ArticleEdit(YuzukiResource):
    @need_anybody_permission
    def render_GET(self, request):
        article_id = request.get_argument("id")
        article = get_article(request, article_id)
        if is_author(request, article):
            context = {"article": replaceArticleContentForEdit(article)}
            return render_template("article_edit.html", request, context)
        else:
            raise Unauthorized()

    @need_anybody_permission
    def render_POST(self, request):
        article_id = request.get_argument("id")
        article = get_article(request, article_id)
        if is_author(request, article):
            subject = request.get_argument("subject")
            content = request.get_argument("content")
            # no empty subject
            if subject.strip():
                edit_article(request, article, subject, content)
                request.dbsession.commit()
                request.redirect("/article/view?id=%s" % article.uid)
                return "article edit success"
            else:
                raise BadRequest()
        else:
            raise Unauthorized()
