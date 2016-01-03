# -*- coding: utf-8 -*-
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from twisted.web.http import RESPONSES

from config.side_menu_conf import SIDE_MENU
from helper.permission import is_anybody
from config.config import SITE_NAME


jinja2_env = Environment(loader=FileSystemLoader("template", encoding="utf-8"),
                         extensions=['jinja2.ext.with_'])
jinja2_env.globals = {
    "site_name": SITE_NAME,
    "datetime": datetime,
    "getattr": getattr,
}


def get_template(name, parent=None, glob=None):
    return jinja2_env.get_template(name, parent, glob)


def render_template(name, request, context=None):
    if context is None:
        context = dict()

    context["side_menu"] = SIDE_MENU
    context["request"] = request
    context["is_anybody"] = is_anybody(request)
    return get_template(name).render(context)


def render_template_from_text(text, context=None):
    if not context:
        context = dict()
    template = jinja2_env.from_string(text)
    return template.render(context).encode("utf-8")


def generate_error_message(request, code, detail):
    brief = RESPONSES[code]
    context = {
        "brief": brief,
        "detail": detail,
        "title": str(code) + " " + str(brief),
    }
    return render_template("error.html", request, context)
