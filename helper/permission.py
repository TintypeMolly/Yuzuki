# -*- coding: utf-8 -*-
def is_anybody(request):
    return request.user and any([group.name == "anybody"
                                 for group in request.user.groups])


def is_admin(request):
    return request.user and request.user.is_admin


def can_write(request, board):
    return request.user and request.user in board.write_group.users


def can_comment(request, board):
    return request.user and request.user in board.comment_group.users


def is_author(request, item):
    return request.user and request.user == item.user


def is_author_or_admin(request, item):
    return is_author(request, item) or is_admin(request)
