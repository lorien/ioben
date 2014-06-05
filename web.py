from threading import Thread
from tornado.ioloop import IOLoop
import tornado.web
import time
import collections
import tornado.gen
import itertools

DATA = open('static/28k.html').read()

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        self.set_status(200)
        self.set_header('Content-Type', 'text/html; charset=utf-8')
        self.write(DATA)

        try:
            delay = float(self.get_argument('delay', 0))
        except ValueError:
            delay = 0

        try:
            num = int(self.get_argument('num', 0))
        except ValueError:
            num = 0

        self.write('%02d' % num)

        if delay:
            yield tornado.gen.Task(IOLoop.instance().add_timeout, time.time() + delay)

        self.finish()

def main():
    app = tornado.web.Application([
        (r"^.*", MainHandler),
    ])
    app._listen_port = 9000
    app.listen(9000)

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
