# -*- coding: utf-8 -*-
from datetime import datetime

from bleach import clean
from sqlalchemy import Boolean, Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from model.base import Base


class Reply(Base):
    __tablename__ = "reply"
    uid = Column(Integer(), primary_key=True)
    article_id = Column(Integer(), ForeignKey("article.uid"), nullable=False)
    article = relationship("Article")
    user_id = Column(Integer(), ForeignKey("user.uid"), nullable=False)
    user = relationship("User", foreign_keys=user_id)
    content = Column(Text())
    enabled = Column(Boolean, default=True)
    is_modified = Column(Boolean, default=False, onupdate=True)
    last_modified = Column(DateTime, onupdate=datetime.now,
                           default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    deleted_at = Column(DateTime)
    deleted_user_id = Column(Integer(), ForeignKey("user.uid"))
    deleted_user = relationship("User", foreign_keys=deleted_user_id)

    def __repr__(self):
        return "<Reply uid=%s, content=%s>" % (self.uid, self.content)

    def to_dict(self):
        data = {
            "uid": self.uid,
            "article_id": self.article_id,
            "user_id": self.user_id,
            "user_nickname": self.user.nickname,
            "content": self.content,
            "is_modified": self.is_modified,
            "created_at": self.created_at.strftime("%y-%m-%d %H:%M:%S"),
        }
        if self.is_modified:
            data["last_modified"] = self.last_modified.strftime(
                "%y-%m-%d %H:%M:%S")
        return data

    def get_cleaned_content(self):
        return clean(self.content, tags=[], strip=True)
