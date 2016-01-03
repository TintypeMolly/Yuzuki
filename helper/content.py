# -*- coding: utf-8 -*-
from markdown import Markdown
from bleach import linkify, callbacks

markdown_extension_list = [
    "extra",
    "admonition",
    "codehilite",
    "nl2br",
    "sane_lists",
    "toc",
    "wikilinks",
]
md = Markdown(extensions=markdown_extension_list)


def markdown_convert(source):
    md.reset()
    return md.convert(source)


def markdown_and_linkify(source):
    source = markdown_convert(source)
    source = linkify(source, parse_email=True,
                     callbacks=[callbacks.nofollow,
                                target_blank_except_footnote])
    return source


def target_blank_except_footnote(attrs, new=False):
    if "class" in attrs and \
       attrs["class"] in ("footnote-backref", "footnote-ref"):
        return attrs
    else:
        return callbacks.target_blank(attrs, new)
