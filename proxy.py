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
import json
import urllib.request
# from arachni import ArachniClient
# from config import scan_server
from utils.parser import ResponseParser
from scan import scan_run
# from lib.database import MYSQL
from pprint import pprint
from mitmproxy import controller, options, master
from mitmproxy.proxy import ProxyServer, ProxyConfig

logging.basicConfig(
    level=logging.WARNING,  # filename='/tmp/wyproxy.log',
    format='%(asctime)s [%(levelname)s] %(message)s',
)


class MyMaster(master.Master):
    def run(self):
        try:
            master.Master.run(self)
        except KeyboardInterrupt:
            self.shutdown()

    @controller.handler
    def request(self, f):
        pass
        # print("request", f)

    @controller.handler
    def response(self, f):
        # print("response", f)
        try:
            if _domain in f.request.host:
                # pprint(f)
                parser = ResponseParser(f)
                result = parser.parser_data()
                task_id = scan_run.delay(result['url'], headers=result['request_header'],
                                         post_data=result['request_content'] or "")
                print(task_id)
                # request = urllib.request.Request(scan_server + '/scan', json.dumps({
                #     "url": result['url'],
                #     "headers": result['request_header'],
                #     "content": result['request_content'] or ""
                # }).encode('utf8'))
                # request.add_header('Content-Type', 'application/json')
                # urllib.request.urlopen(request)
                # 准备celery
                # mysqldb_io = MysqlInterface()
                # mysqldb_io.insert_result(result)
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
