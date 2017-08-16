import hashlib
import re
from urllib.parse import urlparse, parse_qsl, unquote, urlencode, urlunparse


def get_url_hash(url, body):
    url = url_etl(url)
    return hashlib.md5(("%s%s" % (url, body)).encode('utf-8')).hexdigest()


def url_etl(url):
    params_new = {}
    u = urlparse(url)
    path_new = re.sub(r"\d+", "N", u.path)
    query = unquote(u.query)
    # 需要归一化静态页面的id
    if not query:
        url_new = urlunparse((u.scheme, u.netloc, path_new, "", "", ""))
        return url_new
    params = parse_qsl(query, True)
    for k, v in params:
        # 去除无用参数
        if k in ["_", "timestamp"]:
            continue
        # 处理值为空的参数
        if v:
            params_new[k] = etl(v)
    query_new = urlencode(params_new)
    url_new = urlunparse((u.scheme, u.netloc, path_new, u.params, query_new, u.fragment))
    return url_new


def etl(str):
    chars = ""
    for c in str:
        c = c.lower()
        if ord('a') <= ord(c) <= ord('z'):
            chars += 'A'
        elif ord('0') <= ord(c) <= ord('9'):
            chars += 'N'
        elif c in [',', '-', '_']:
            chars += 'T'
        else:
            chars += 'C'
    chars = re.sub(r"N{1,}", "N", chars)
    return chars
