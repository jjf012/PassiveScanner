# from __future__ import absolute_import

import base64
import re
# import mimetypes
from config import media_types, static_files, static_ext, save_content


class ResponseParser(object):
    """docstring for ResponseParser"""

    def __init__(self, f):
        super(ResponseParser, self).__init__()
        self.flow = f
        # self.content_type = self.get_content_type()
        # self.extension = self.get_extension()
        # self.ispass = self.capture_pass()

    def parser_data(self):
        """parser the capture response & request"""
        result = dict()
        # result['content_type'] = self.content_type
        result['url'] = self.flow.request.url
        result['path'] = '/{}'.format('/'.join(self.flow.request.path_components))
        # result['extension'] = self.get_extension()
        result['host'] = self.flow.request.host
        result['port'] = self.flow.request.port
        result['scheme'] = self.flow.request.scheme
        result['method'] = self.flow.request.method
        result['status_code'] = self.flow.response.status_code
        # result['date_start'] = self.flow.response.timestamp_start
        # result['date_end'] = self.flow.response.timestamp_end
        result['content_length'] = int(self.flow.response.headers.get('Content-Length', 0))
        # result['static_resource'] = self.ispass
        # result['resp_header'] = self.parser_header(self.flow.response.headers)
        result['request_header'] = self.parser_header(self.flow.request.headers)

        # request resource is media file & static file, so pass
        # if self.ispass:
        # result['resp_content'] = None
        # result['request_content'] = None
        # return result

        # result['resp_content'] = self.flow.response.content if save_content else ''
        # result['request_content'] = self.get_request_content() if save_content else ''
        result['request_content'] = self.flow.request.content
        return result

    # def get_content_type(self):
    #     if not self.flow.response.headers.get('Content-Type'):
    #         return ''
    #     return self.flow.response.headers.get('Content-Type').split(';')[:1][0]

    # def get_content_length(self):
    #     if self.flow.response.headers.get('Content-Length'):
    #         return int(self.flow.response.headers.get('Content-Length'))
    #     else:
    #         return 0

    # def capture_pass(self):
    #     """if content_type is media_types or static_files, then pass captrue"""
    #
    #     if self.extension in static_ext:
    #         return True
    #
    #     # can't catch the content_type
    #     if not self.content_type:
    #         return False
    #
    #     if self.content_type in static_files:
    #         return True
    #
    #     http_mime_type = self.content_type.split('/')[:1]
    #     if http_mime_type:
    #         return True if http_mime_type[0] in media_types else False
    #     else:
    #         return False

    # def get_request_content(self):
    #     content = self.flow.request.content
    #     if 'multipart/form-data' in self.parser_header(self.flow.request.headers).get('Content-Type', ''):
    #         content = self.decode_response_text(content)
    #         return self.parser_multipart(content)
    #     else:
    #         return content

    # def get_header(self):
    #     return self.parser_header(self.flow.response.headers)

    # def get_content(self):
    #     return self.flow.response.content

    # def get_request_header(self):
    #     return self.parser_header(self.flow.request.headers)

    # def get_url(self):
    #     return self.flow.request.url

    # def get_path(self):
    #     return '/{}'.format('/'.join(self.flow.request.path_components))

    # def get_scheme(self):
    #     return self.flow.request.scheme
    #
    # def get_method(self):
    #     return self.flow.request.method

    # def get_port(self):
    #     return self.flow.request.port
    #
    # def get_host(self):
    #     return self.flow.request.host

    # def get_status_code(self):
    #     return self.flow.response.status_code

    # def get_extension(self):
    #     if not self.flow.request.path_components:
    #         return ''
    #     else:
    #         end_path = self.flow.request.path_components[-1:][0]
    #         split_ext = end_path.split('.')
    #         if not split_ext or len(split_ext) == 1:
    #             return ''
    #         else:
    #             return split_ext[-1:][0][:32]

    @staticmethod
    def parser_multipart(content):
        if isinstance(content, str):
            res = re.findall(r'name=\"(\w+)\"\r\n\r\n(\w+)', content)
            if res:
                return "&".join([k + '=' + v for k, v in res])
            else:
                return ""
        else:
            return ""

    @staticmethod
    def parser_header(header):
        headers = {}
        for key, value in header.items():
            headers[key] = value
        return headers

    @staticmethod
    def decode_response_text(content):
        for _ in ['UTF-8', 'GB2312', 'GBK', 'iso-8859-1', 'big5']:
            try:
                return content.decode(_)
            except:
                continue
        return content
