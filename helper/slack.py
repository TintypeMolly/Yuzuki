# -*- coding: utf-8 -*-
import json
import urllib

from bleach import clean
from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from config.config import SLACK_NOTI_CHANNEL, SLACK_POST_INFO,\
    SLACK_NOTI_TARGET_BOARDS

SLACK_CHAT_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)

contextFactory = WebClientContextFactory()
agent = Agent(reactor, contextFactory)


def post_message(request, article, article_view_url):
    if article.board.repr not in SLACK_NOTI_TARGET_BOARDS:
        return
    article_link = "%s://%s%s".format(request.getProto(),
                                      request.getRequestHostname(),
                                      article_view_url)
    content = clean(article.compiled_content, tags=[], strip=True)
    if len(content) > 30:
        content = content[:27] + "..."
    params = {
        "text": u"%s에 새 글이 등록되었습니다." % article.board.repr,
        "channel": SLACK_NOTI_CHANNEL,
    }
    params.update(SLACK_POST_INFO)
    attachments = list()
    attachments.append({
        "title": article.subject,
        "title_link": article_link,
        "text": content,
        "author_name": article.user.nickname,
    })
    params["attachments"] = json.dumps(attachments)
    params = {key: params[key].encode("utf-8")
              if type(params[key]) in (unicode, str) else params[key]
              for key in params}
    get_args = urllib.urlencode(params)

    d = agent.request(
        "GET",
        "https://slack.com/api/chat.postMessage?" + get_args,
        Headers({"User-Agent": ["Twisted Web Server Slack Notify"]}),
        None
    )
    d.addBoth(slack_callback, request)


def slack_callback(resp, request):
    d = readBody(resp)
    d.addCallback(slack_resp, request)


def slack_resp(resp_body, request):
    response = json.loads(resp_body)
    if not response["ok"]:
        request.logger.error("Slack post message error : %s",
                             response["error"])
