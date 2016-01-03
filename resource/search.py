# -*- coding: utf-8 -*-
from sqlalchemy.orm import subqueryload
from sqlalchemy import or_

from config.config import ARTICLE_PER_PAGE
from exception import BadRequest
from helper.model_control import get_board
from helper.resource import YuzukiResource, need_anybody_permission
from helper.template import render_template
from model.article import Article
from model.reply import Reply
from model.user import User


class Search(YuzukiResource):
    @need_anybody_permission
    def render_GET(self, request):
        query_string = request.get_argument("query")
        search_type = request.get_argument("type", "content")
        target = request.get_argument("target", "article")
        if search_type not in ["user", "content"] or\
           target not in ["article", "reply"]:
            raise BadRequest()

        board_name = request.get_argument("board", None)
        board = get_board(request, board_name) if board_name else None

        page = request.get_argument_int("page", 1)

        if search_type == "content":
            query_words = ["%" + word + "%"
                           for word in query_string.split(" ")]
            expr_list = list()
            if target == "article":
                for word in query_words:
                    expr_list.append(Article.subject.like(word))
                    expr_list.append(Article.content.like(word))
                query = request.dbsession.query(Article)\
                                         .filter(or_(*expr_list))\
                                         .options(subqueryload(Article.user))\
                                         .options(subqueryload(Article.board))
            else:
                for word in query_words:
                    expr_list.append(Reply.content.like(word))
                query = request.dbsession.query(Reply)\
                                         .filter(or_(*expr_list))\
                                         .options(subqueryload(Reply.user))
        else:
            query = request.dbsession.query(User)\
                                     .filter(User.nickname == query_string)
            result = query.all()
            target_user = result[0] if result else None
            if target == "article":
                query = request.dbsession.query(Article)\
                                         .filter(Article.user == target_user)\
                                         .options(subqueryload(Article.board))\
                                         .options(subqueryload(Article.user))
            else:
                query = request.dbsession.query(Reply)\
                                         .filter(Reply.user == target_user)\
                                         .options(subqueryload(Reply.article)
                                                  .subqueryload(Article.board))

        item_per_page = ARTICLE_PER_PAGE
        start_idx = item_per_page * (page - 1)
        end_idx = item_per_page * page
        items = query[start_idx:end_idx]
        total_item_count = query.count()
        page_total = total_item_count / item_per_page
        if total_item_count % item_per_page != 0:
            page_total += 1
        render_page = "search_article.html"\
            if target == "article" else "search_reply.html"
        context = {
            "query": query_string,
            "type": search_type,
            "target": target,
            "board": board,
            "page": page,
            "page_total": page_total,
            "items": items,
        }
        return render_template(render_page, request, context)
