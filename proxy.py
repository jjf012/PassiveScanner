#!/usr/bin/env python3
"""
    This example shows how to build a proxy based on mitmproxy's Flow
    primitives.
    Heads Up: In the majority of cases, you want to use inline scripts.
    Note that request and response messages are not automatically replied to,
    so we need to implement handlers to do this.
"""
import argparse
import logging
import redis
from pprint import pprint
from mitmproxy import controller, options, master
from mitmproxy.proxy import ProxyServer, ProxyConfig
from config import media_types, static_files, static_ext
from scan import scan_run
from utils.parser import ResponseParser
from utils.utils import get_url_hash

logging.basicConfig(
    level=logging.INFO,  # filename='/tmp/wyproxy.log',
    format='%(asctime)s [%(levelname)s] %(message)s',
)
r = redis.Redis(host="localhost", port=6379, password="password")


class MyMaster(master.Master):
    def __init__(self, *args, **kwargs):
        super(MyMaster, self).__init__(*args, **kwargs)
        # self.url_seen = set()

    def run(self):
        try:
            logging.info("proxy started successfully...")
            master.Master.run(self)
        except KeyboardInterrupt:
            logging.info("Ctrl C - stopping proxy")
            self.shutdown()

    def get_extension(self, flow):
        if not flow.request.path_components:
            return ''
        else:
            end_path = flow.request.path_components[-1:][0]
            split_ext = end_path.split('.')
            if not split_ext or len(split_ext) == 1:
                return ''
            else:
                return split_ext[-1:][0][:32]

    def capture_pass(self, flow):
        """if content_type is media_types or static_files, then pass captrue"""

        extension = self.get_extension(flow)
        if extension in static_ext:
            return True

        # can't catch the content_type
        content_type = flow.response.headers.get('Content-Type', '').split(';')[:1][0]
        if not content_type:
            return False

        if content_type in static_files:
            return True

        http_mime_type = content_type.split('/')[:1]
        if http_mime_type:
            return True if http_mime_type[0] in media_types else False
        else:
            return False

    @controller.handler
    def request(self, f):
        pprint(f.request.path_components)

    @controller.handler
    def response(self, f):
        try:
            # if _domain in f.request.host:
            if not self.capture_pass(f):
                url_id = get_url_hash(f.request.url, f.request.content)
                if not r.exists(url_id):
                    # pprint(result)
                    r.set(url_id, 1)
                    parser = ResponseParser(f)
                    result = parser.parser_data()
                    task_id = scan_run.delay(result['url'], headers=result['request_header'],
                                             post_data=result['request_content'] or "")
                    print(task_id)
        except Exception as e:
            logging.error(e)

    @controller.handler
    def error(self, f):
        print("error", f)

    @controller.handler
    def log(self, l):
        print("log", l.msg)


def start_server(port, mode, domain):
    if mode == "http":
        mode = "regular"
    opts = options.Options(
        cadir="~/.mitmproxy/",
        listen_port=int(port) or 8080,
        mode=mode
    )
    if domain:
        global _domain
        _domain = domain
    config = ProxyConfig(opts)
    server = ProxyServer(config)
    m = MyMaster(opts, server)
    m.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="myProxy v 1.0 ( Proxying And Recording HTTP/HTTPs and Socks5)")
    parser.add_argument("-m", "--mode", metavar="", choices=['http', 'socks5', 'transparent'], default="http",
                        help="wyproxy mode (HTTP/HTTPS, Socks5, Transparent)")
    parser.add_argument("-p", "--port", metavar="", default="8080",
                        help="wyproxy bind port")
    parser.add_argument("-d", "--domain", metavar="", default="",
                        help="include domain")
    args = parser.parse_args()
    start_server(args.port, args.mode, args.domain)
