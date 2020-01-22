#!/usr/bin/env python3
# vim: set fileencoding=utf8 :

"""
This example demonstrates adding rudementary API authentication

More advanced authentication and security practices can be seen here:
https://www.tornadoweb.org/en/stable/guide/security.html
"""

import tornado.ioloop
from tornado.options import options, define

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import tornado_jsonapi.handlers
import tornado_jsonapi.resource
import tornado_jsonapi.exceptions
import status

Base = declarative_base()

class AuthAPIHAndler(tornado_jsonapi.handlers.APIHandler):
    """
    A simple API handler that requires an API Key in order to GET
    """

    @tornado.gen.coroutine
    def get(self, id_=None):
        try:
            if 'api' in self.request.arguments and self.request.arguments['api'][0].decode() == "deadbeef":
                return tornado_jsonapi.handlers.APIHandler.get(self, id_)
        except:
            pass
        raise tornado_jsonapi.exceptions.APIError(status.HTTP_400_BAD_REQUEST, "Invalid API Key")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    author = Column(String)
    text = Column(String)
    hideMe = Column(DateTime)
    hideMe2 = Column(String, default="secret")


def main():
    define("debug", default=False, help="Run in debug mode")
    options.parse_command_line()
    settings = {}
    settings.update(options.group_dict(None))
    settings.update(tornado_jsonapi.handlers.not_found_handling_settings())
    settings.update({"jsonapi_limit": 12})

    engine = create_engine("sqlite:///:memory:", echo=settings["debug"])
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    s = Session()
    for i in range(1, 16):
        p = Post()
        p.author = "Author %d" % i
        p.text = "Text for %d" % i
        s.add(p)
    s.commit()

    postResource = tornado_jsonapi.resource.SQLAlchemyResource(Post, Session)
    postResource.blacklist.append(Post.hideMe)
    postResource.blacklist.append("hideMe2")

    application = tornado.web.Application(
        [
            (
                r"/api/posts/([^/]*)",
                AuthAPIHAndler,
                dict(resource=postResource),
            ),
        ],
        **settings
    )
    application.listen(8888)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
