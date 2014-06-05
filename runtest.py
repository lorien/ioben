#!/usr/bin/env python
"""
* Grab::Spider
* gevent & urllib
* gevent & urllib2 
* threading & urllib
* threading & urllib2
todo:
* gevent & urllib3
* gevent & httplib
* gevent & geventhttpclient
* multicurl
* tornado & its http client
* twisted

deps:
* lxml
* pycurl
* argparse
* gevent
"""
import sys
import time
import logging
import argparse
from random import randint
from collections import deque

URLS = (
    #('http://localhost:9000/?delay=0.5', 100, [100, 1000]),
    ('http://localhost:9000/?delay=0', 2000, [50, 100, 500, 1000]),
)
DATA_FILE = open('static/28k.fast.html').read()
DATA_START = DATA_FILE[:20]
COUNTER = deque()

def process_response(data):
    assert data.startswith(DATA_START)
    num = int(data[-2:])
    COUNTER.append(num)


def generate_task_list(url, count):
    task_list = deque()
    for x in xrange(count):
        num = randint(1, 10)
        task_list.append((num, url + '&num=%d' % num))
    return task_list


def test_spider(task_list, thread_count):
    from grab.spider import Spider, Task

    class TestSpider(Spider):
        def task_generator(self):
            for num, url in task_list:
                yield Task('page', url=url)

        def task_page(self, grab, task):
            self.meta['callback'](grab.response.body)

    bot = TestSpider(thread_number=thread_count)
    bot.meta['callback'] = process_response
    bot.run()


def test_gevent_urllib(task_list, thread_count):
    if 'threading' in sys.modules:
        del sys.modules['threading']
    import urllib
    import gevent
    import gevent.monkey

    gevent.monkey.patch_all()

    def crawler():
        while True:
            try:
                num, url = task_list.pop()
            except IndexError:
                return
            else:
                data = urllib.urlopen(url).read()
                process_response(data)

    glets = []
    for x in xrange(thread_count):
        glet = gevent.spawn(crawler)
        glets.append(glet)
    gevent.joinall(glets)


def test_gevent_urllib2(task_list, thread_count):
    if 'threading' in sys.modules:
        del sys.modules['threading']
    import urllib2
    import gevent
    import gevent.monkey

    gevent.monkey.patch_all()

    def crawler():
        while True:
            try:
                num, url = task_list.pop()
            except IndexError:
                return
            else:
                data = urllib2.urlopen(url).read()
                process_response(data)

    glets = []
    for x in xrange(thread_count):
        glet = gevent.spawn(crawler)
        glets.append(glet)
    gevent.joinall(glets)


def test_threading_urllib(task_list, thread_count):
    import threading
    import urllib

    def crawler():
        while True:
            try:
                num, url = task_list.pop()
            except IndexError:
                return
            else:
                data = urllib.urlopen(url).read()
                process_response(data)

    threads = []
    for x in xrange(thread_count):
        thread = threading.Thread(target=crawler)
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


def test_threading_urllib2(task_list, thread_count):
    import threading
    import urllib2

    def crawler():
        while True:
            try:
                num, url = task_list.pop()
            except IndexError:
                return
            else:
                data = urllib2.urlopen(url).read()
                test_num = int(data[-2:])
                assert test_num == num
                process_response(data)

    threads = []
    for x in xrange(thread_count):
        thread = threading.Thread(target=crawler)
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


def test_gevent_urllib3(task_list, thread_count):
    if 'threading' in sys.modules:
        del sys.modules['threading']
    import urllib3
    import gevent
    import gevent.monkey

    gevent.monkey.patch_all()
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

    conn = urllib3.connection_from_url(task_list[0][1], maxsize=thread_count)

    def crawler():
        while True:
            try:
                num, url = task_list.pop()
            except IndexError:
                return
            else:
                res = conn.request('GET', url)
                process_response(res.data)

    glets = []
    for x in xrange(thread_count):
        glet = gevent.spawn(crawler)
        glets.append(glet)
    gevent.joinall(glets)


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('backend')
    args = parser.parse_args()
    func = globals()['test_%s' % args.backend]
    print 'Testing %s' % func.__name__
    for url, req_count, con_options in URLS:
        # Warm-up
        func(generate_task_list(url, 1), 1)

        print '- Testing %s' % url
        print '- Request count: %d' % req_count
        for con_count in con_options:
            # Prepare test environment
            COUNTER.clear()
            task_list = generate_task_list(url, req_count)
            expected_counter = sum(x[0] for x in task_list)

            # Start test!
            start_time = time.time()
            func(task_list, con_count)
            total_time = time.time() - start_time

            print '  - Concurrency: %d, time: %.2f' % (con_count, total_time)
            assert sum(COUNTER) == expected_counter


if __name__ == '__main__':
    main()
