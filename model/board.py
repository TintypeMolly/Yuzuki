# -*- coding: utf-8 -*-
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from model.base import Base


class Board(Base):
    __tablename__ = "board"
    uid = Column(Integer(), primary_key=True)
    name = Column(String(255), index=True, nullable=False, unique=True)
    repr = Column(String(255), nullable=False)
    repr_order = Column(Integer())
    classification = Column(String(255), index=True)
    write_group_uid = Column(Integer(), ForeignKey("group.uid"))
    write_group = relationship("Group", foreign_keys=write_group_uid)
    comment_group_uid = Column(Integer(), ForeignKey("group.uid"))
    comment_group = relationship("Group", foreign_keys=comment_group_uid)
    description = Column(String(255))
    article_count = Column(Integer(), default=0)
    enabled = Column(Boolean(), default=True)
    articles = relationship("Article")

    def __init__(self, name, repr, write_group, comment_group,
                 classification=None, order=None):
        self.name = name
        self.repr = repr
        self.write_group = write_group
        self.comment_group = comment_group
        self.classification = classification
        self.order = order

    def __repr__(self):
        return "<Board name=%s>" % self.name
