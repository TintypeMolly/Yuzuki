# -*- coding: utf-8 -*-
import copy
from datetime import datetime, timedelta
from urllib import quote

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import subqueryload
from twisted.python.compat import intToBytes
from twisted.web.http import INTERNAL_SERVER_ERROR
from twisted.web.server import Request

from config.config import DEBUG
from exception import YuzukiException, BadRequest
from helper.database import DatabaseHelper
from helper.template import generate_error_message
from model.user import User


class NoArgument:
    pass


class YuzukiRequest(Request):
    dbsession = DatabaseHelper.session()

    def initialize(self, resource):
        """
        if you need to do something just before or just after a request is
        initialized, write it here
        """
        self._initial_session = copy.deepcopy(self.yzk_session)
        auto_login = "auto_id" in self.received_cookies and\
                     "auto_pw" in self.received_cookies
        if auto_login:
            username = self.getCookie("auto_id")
            password = self.getCookie("auto_pw")
            if self.user is None:
                query = self.dbsession.query(User)\
                                      .filter(User.username == username)
                result = query.all()
                if result:
                    user = result[0]
                    if user.check_password(password):
                        self.log_user_in(user)
                    else:
                        self.remove_auto_login_cookie()
                else:
                    self.remove_auto_login_cookie()
            else:
                username = self.getCookie("auto_id")
                password = self.getCookie("auto_pw")
                if self.user.username == username and\
                   self.user.check_password(password):
                    # refresh auto login cookie expire time
                    self.set_auto_login(username, password)

    def remove_auto_login_cookie(self):
        expires_date = datetime.now() - timedelta(days=2)
        expires = expires_date.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        self.addCookie("auto_id", "", expires=expires, path="/")
        self.addCookie("auto_pw", "", expires=expires, path="/")

    def set_auto_login(self, username, password):
        username = username.encode("utf-8")
        password = password.encode("utf-8")
        expires_date = datetime.now() + timedelta(days=2)
        expires = expires_date.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        self.addCookie("auto_id", username, expires=expires, path="/")
        self.addCookie("auto_pw", password, expires=expires, path="/")

    def finalize(self):
        """
        if you need to do something just before or just after a request is
        finished, write it here
        """
        if self._initial_session != self.yzk_session:
            self.session.redis_sync()

    @property
    def yzk_session(self):
        twisted_session = self.getSession()
        if not hasattr(twisted_session, "yuzuki_session_data"):
            twisted_session.yuzuki_session_data = dict()
        return twisted_session.yuzuki_session_data

    def log_user_in(self, user):
        self.yzk_session["login_user"] = user.uid

    def log_user_out(self):
        if "login_user" in self.yzk_session:
            del self.yzk_session["login_user"]

    def _is_user_logged_in(self):
        return "login_user" in self.yzk_session

    @property
    def user(self):
        if hasattr(self, "_user"):
            return self._user
        user_id = self.yzk_session["login_user"] \
            if self._is_user_logged_in()else None
        if not user_id:
            return None
        else:
            query = self.dbsession.query(User)\
                                  .filter(User.uid == user_id)\
                                  .options(subqueryload(User.groups))
            result = query.all()
            user = result[0]
            self._user = user
            return user

    def get_argument(self, key, default=NoArgument):
        args = self.args.get(key, None)
        if not args:
            if default == NoArgument:
                raise BadRequest()
            else:
                return default
        else:
            if len(args) == 1:
                return unicode(args[0], "utf8")
            else:
                raise BadRequest()

    def get_argument_int(self, key, default=NoArgument):
        try:
            value = self.get_argument(key, default)
            return int(value)
        except ValueError:
            if default != NoArgument:
                return default
            else:
                raise BadRequest()

    def get_path_and_query(self):
        result = self.path
        if self.args:
            result += "?"
            for i, key in enumerate(self.args):
                for j, value in enumerate(self.args[key]):
                    result += key
                    result += "="
                    result += quote(value, "")
                    if not (i == len(self.args) - 1 and
                            j == len(self.args[key]) - 1):
                        result += "&"
        return result

    def processingFailed(self, reason):
        if DEBUG:
            return Request.processingFailed(self, reason)
        else:
            if issubclass(reason.type, YuzukiException):
                exc = reason.value
                self.logger.warning(reason)
                self.setResponseCode(exc.status)
                body = generate_error_message(self, exc.status, exc.message)
            else:
                self.logger.error(reason)
                self.setResponseCode(INTERNAL_SERVER_ERROR)
                body = generate_error_message(self, INTERNAL_SERVER_ERROR,
                                              u"서버 에러가 발생하였습니다.")
            if issubclass(reason.type, SQLAlchemyError):
                YuzukiRequest.dbsession.close()
                YuzukiRequest.dbsession = DatabaseHelper.session()
            body = body.encode("UTF-8")
            self.setHeader(b'content-type', b"text/html")
            self.setHeader(b'content-length', intToBytes(len(body)))
            self.write(body)
            self.finish()
            return reason

    def redirect(self, url):
        if isinstance(url, unicode):
            url = url.encode("UTF-8")
        Request.redirect(self, url)

    def getClientIP(self):
        real_ip = self.getHeader("X-Real-IP")
        if real_ip:
            return real_ip
        else:
            Request.getClientIP(self)

    def setNoCache(self):
        self.setHeader("Cache-Control", "no-cache, no-store, must-revalidate")
        self.setHeader("Pragma", "no-cache")
        self.setHeader("Expires", "0")

    def getProto(self):
        if self.requestHeaders.hasHeader("X-Forwarded-Proto"):
            return self.getHeader("X-Forwarded-Proto").lower()
        else:
            return "https" if self.isSecure() else "http"
