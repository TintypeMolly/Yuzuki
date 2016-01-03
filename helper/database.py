# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.config import DB_CONNECTION_STRING
from model.base import Base


# import all models you defined here
from model.association.user_group import UserGroupAssociation  # noqa
from model.article import Article  # noqa
from model.article_record import ArticleRecord  # noqa
from model.board import Board  # noqa
from model.chat import Chat  # noqa
from model.chat_kv import ChatKV  # noqa
from model.group import Group  # noqa
from model.metadata import MetaData  # noqa
from model.reply import Reply  # noqa
from model.reply_record import ReplyRecord  # noqa
from model.user import User  # noqa


class DatabaseHelper(object):
    _engine = create_engine(DB_CONNECTION_STRING, pool_recycle=3600)
    _Session = sessionmaker(bind=_engine)

    @classmethod
    def engine(cls):
        return cls._engine

    @classmethod
    def session(cls):
        return cls._Session()

    @classmethod
    def create_all(cls):
        Base.metadata.create_all(cls._engine)

    @classmethod
    def drop_all(cls):
        Base.metadata.drop_all(cls._engine)
