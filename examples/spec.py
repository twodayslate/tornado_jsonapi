#!/usr/bin/env python3
# vim: set fileencoding=utf8 :

import tornado.ioloop
from tornado.options import options, define

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import tornado_jsonapi.handlers
import tornado_jsonapi.resource
import copy

Base = declarative_base()


class APISpecHandler(tornado.web.RequestHandler):
    def initialize(self, resource) -> None:
        self.resource = resource

    def get(self):
        print(self.resource.schema)

        schema = copy.deepcopy(self.resource.schema)

        for i in self.resource.blacklist:
            if not isinstance(i, str):
                schema["properties"].pop(str(i).split(".")[-1], None)
            else:
                schema["properties"].pop(i, None)

        self.write(schema)


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
        [(r"/posts/spec.json", APISpecHandler, dict(resource=postResource),),],
        **settings
    )
    application.listen(8888)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
