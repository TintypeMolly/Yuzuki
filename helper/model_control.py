# -*- coding: utf-8 -*-
from datetime import datetime

from bleach import clean, linkify, callbacks
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.expression import true

from config.config import ARTICLE_PER_PAGE, REPLY_PER_PAGE, CHAT_PER_PAGE
from exception import PageNotFound
from model.article import Article
from model.article_record import ArticleRecord
from model.board import Board
from model.chat import Chat
from model.chat_kv import ChatKV
from model.group import Group
from model.reply import Reply
from model.reply_record import ReplyRecord
from model.user import User
from model.association.user_group import UserGroupAssociation


def get_board(request, board_name):
    query = request.dbsession.query(Board).filter(Board.name == board_name)
    result = query.all()
    if not result:
        raise PageNotFound()
    board = result[0]
    if not board.enabled:
        raise PageNotFound()
    return board


def get_article(request, article_id):
    query = request.dbsession.query(Article)\
                             .filter(Article.uid == article_id)\
                             .filter(Article.enabled == true())\
                             .options(subqueryload(Article.board))\
                             .options(subqueryload(Article.user))
    result = query.all()
    if not result:
        raise PageNotFound()
    article = result[0]
    if not article.board.enabled:
        raise PageNotFound()
    return article


def delete_article(request, article):
    article.enabled = False
    article.deleted_at = datetime.now()
    article.deleted_user = request.user
    article.board.article_count -= 1


def edit_article(request, article, subject, content):
    article_record = ArticleRecord(article)
    article.subject = subject
    article.change_content(content)
    article.is_modified = True
    article.last_modified = datetime.now()
    request.dbsession.add(article_record)


def get_article_page(request, board, page):
    query = request.dbsession.query(Article)\
                             .filter(Article.enabled == true())\
                             .filter(Article.board == board)\
                             .order_by(Article.uid.desc())\
                             .options(subqueryload(Article.user))
    start_idx = ARTICLE_PER_PAGE * (page - 1)
    end_idx = ARTICLE_PER_PAGE + start_idx
    return query[start_idx:end_idx]


def get_reply_page(request, article, page):
    query = request.dbsession.query(Reply)\
                             .filter(Reply.enabled == true())\
                             .filter(Reply.article == article)\
                             .order_by(Reply.uid.asc())\
                             .options(subqueryload(Reply.user))
    start_idx = REPLY_PER_PAGE * (page - 1)
    end_idx = REPLY_PER_PAGE + start_idx
    replies = query[start_idx:end_idx]
    return replies


def get_reply(request, reply_id):
    query = request.dbsession.query(Reply)\
                             .filter(Reply.uid == reply_id)\
                             .filter(Reply.enabled == true())\
                             .options(subqueryload(Reply.user))\
                             .options(subqueryload(Reply.article)
                                      .subqueryload(Article.board))
    result = query.all()
    if not result:
        raise PageNotFound()
    reply = result[0]
    if not reply.article.enabled or not reply.article.board.enabled:
        raise PageNotFound()
    return reply


def delete_reply(request, reply):
    reply.enabled = False
    reply.deleted_at = datetime.now()
    reply.deleted_user = request.user
    reply.article.reply_count -= 1


def edit_reply(request, reply, content):
    reply_record = ReplyRecord(reply)
    reply.content = linkify(clean(content, tags=list()), parse_email=True,
                            callbacks=[callbacks.nofollow,
                                       callbacks.target_blank])
    request.dbsession.add(reply_record)


def create_article(request, board, subject, content):
    article = Article()
    article.board = board
    board.article_count += 1
    article.user = request.user
    article.subject = subject
    article.change_content(content)
    return article


def create_reply(request, article, content):
    reply = Reply()
    reply.article = article
    article.reply_count += 1
    reply.user = request.user
    reply.content = linkify(clean(content, tags=list()), parse_email=True,
                            callbacks=[callbacks.nofollow,
                                       callbacks.target_blank])
    return reply


def create_chat(request, content, speaker=None):
    chat = Chat()
    chat.user = speaker if speaker else request.user
    chat.content = linkify(clean(content, tags=list()), parse_email=True,
                           callbacks=[callbacks.nofollow,
                                      callbacks.target_blank])
    return chat


def get_chat_page(request, page):
    query = request.dbsession.query(Chat)\
                             .order_by(Chat.uid.desc())\
                             .options(subqueryload(Chat.user))
    start_idx = CHAT_PER_PAGE * (page - 1)
    end_idx = CHAT_PER_PAGE + start_idx
    return query[start_idx:end_idx]


def get_chat_newer_than(request, chat_id):
    query = request.dbsession.query(Chat)\
                             .filter(Chat.uid > chat_id)\
                             .order_by(Chat.uid.desc())\
                             .options(subqueryload(Chat.user))
    return query[0:CHAT_PER_PAGE]


def get_not_anybody_user(request):
    anybody_query = request.dbsession.query(Group.uid)\
                                     .filter(Group.name == "anybody")\
                                     .subquery()
    assoc_query = request.dbsession.query(UserGroupAssociation.user_id).filter(
        UserGroupAssociation.group_id == anybody_query).subquery()
    query = request.dbsession.query(User)\
                             .filter(User.uid.notin_(assoc_query))\
                             .options(subqueryload(User.bunryu))
    return query.all()


def get_chat_kv(request, key):
    query = request.dbsession.query(ChatKV)\
                             .filter(ChatKV.key == key)\
                             .options(subqueryload(ChatKV.user))
    result = query.all()
    if result:
        return result[0]
    else:
        return None


def set_chat_kv(request, key, value):
    query = request.dbsession.query(ChatKV)\
                             .filter(ChatKV.key == key)\
                             .options(subqueryload(ChatKV.user))
    result = query.all()
    if result:
        kv = result[0]
    else:
        kv = ChatKV()
        request.dbsession.add(kv)
    kv.key = key
    kv.value = linkify(clean(value, tags=list()), parse_email=True,
                       callbacks=[callbacks.nofollow, callbacks.target_blank])
    kv.user = request.user
    return kv


def search_chat_kv_by_key(request, search_word):
    query = request.dbsession.query(ChatKV)\
                             .filter(ChatKV.key.like("%" + search_word + "%"))
    return query.all()


def search_chat_kv_by_value(request, search_word):
    query = request.dbsession.query(ChatKV)\
                             .filter(ChatKV.value.like(
                                 "%" + search_word + "%"))
    return query.all()
