import time
import yaml
import urllib.parse
from celery import Celery
from arachni import ArachniClient
from utils.database import MYSQL
from config import mysqldb_conn
from urllib.parse import parse_qs

app = Celery('tasks')
app.conf.update(
    BROKER_URL='redis://:password@localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://:password@localhost:6379/1',
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    CELERY_MESSAGE_COMPRESSION='zlib',
    CELERY_TIMEZONE='Asia/Shanghai',
    CELERY_ENABLE_UTC=True,
)
m = MYSQL(mysqldb_conn['host'], mysqldb_conn['user'], mysqldb_conn['password'], mysqldb_conn['db'],
          mysqldb_conn['charset'])
a = ArachniClient()
a.profile('./profiles/default.json')


# class config:
#     BROKER_URL = 'redis://localhost:6379/0'
#     CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
#     CELERY_TASK_SERIALIZER = 'json'
#     CELERY_ACCEPT_CONTENT = ['json']
#     CELERY_MESSAGE_COMPRESSION = 'zlib'
#     CELERY_DISABLE_RATE_LIMITS = True
#     # CELERYD_PREFETCH_MULTIPLIER = 1
#     CELERY_TASK_RESULT_EXPIRES = 3600
#     CELERY_TIMEZONE = 'Asia/Shanghai'
#
#
# app.config_from_object(config)




@app.task
def scan_run(url, post_data=None, cookie=None, headers=None):
    """
    函数说明
    :param url: 
    :param post_data: 传入post参数，字典或字符串均可，字符串会尝试转换成字典
    :param cookie: 字符串
    :param headers: 必须为字典
    :return: 暂无返回值
    {
      "url" : null,   // 扫描链接，必须
      "checks" : ["sql*", "xss*", "csrf"], // 必须，扫描的漏洞类型，支持通配符 * ，和反选 -xss*，即不扫描所有类型的 xss
      "http" : { // http请求相关配置，比如设置 cookie 和 header
        "user_agent" : "Arachni/v2.0dev",
        "request_headers" : {},
        "cookie_string" : {} // 请求中的完整 cookie 字段
      }, 
      "audit" : {  // 扫描相关配置，比如哪些参数需要扫描，是否要对 cookie，json 进行扫描等
        "exclude_vector_patterns" : [], # 排除submit参数
        "include_vector_patterns" : [], # 只检测指定参数
        "forms": true,  // 扫描 表单
        "cookies": true,  // 扫描 cookies
        "headers": true, // 扫描 headers
      },
      "input" : { // 设置请求参数的值
        "values" : {}
      },  
      "scope" : {  // 扫描范围相关，比如限制爬取页面数，限制扫描url路径
        "page_limit" : 5,
        "path_exclude_pattern" : []
      },
      "session" : {}, // 登录会话管理，如当前会话有效性验证
      "plugins" : {}  // 插件，比如设置自动登录，指定请求参数进行扫描
    }
    """
    options = {
        "checks": ["sql*", "xss*", "xst", "xxe", "xpath_injection", "os*", "code*", "backup_*", "path_traversal",
                   "file_inclusion",
                   "directory_listing"],
        "audit": {
            "parameter_values": True,
            "exclude_vector_patterns": ["Submit", "submit", "t", "_", "callback", "jsoncallback"],
            "include_vector_patterns": [],
            "link_templates": [],
            "links": True,
            "forms": True,
            "headers": False,
            "cookies": False,
            "jsons": True,
            "xmls": True,
            "ui_forms": False,
            "ui_inputs": False
        },
        "scope": {
            "page_limit": 0
        },
        "browser_cluster": {
            "pool_size": 0
        },
        "http": {
            "request_headers": headers or {},
            "cookie_string": cookie
        }
    }
    if headers and isinstance(headers, dict):
        options.update({
            "http": {
                "request_headers": headers
            }
        })
    if post_data:
        post_dict = {
            "type": "form",
            "method": "post",
            "action": url,
            "inputs": {},
            # "enctype": "multipart/form-data"  没用
        }
        # 设置multipart/form-data仍然还是无效
        # if True:
        #     options['http']['request_headers'].update({
        #         "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryHdbb6xFDw07oyudv"
        #     })
        #if isinstance(post_data, str):
        #    for i in post_data.split('&'):
        #        if i.find('=') > 0:
        #            _i = i.split('=')
        #            key = _i[0]
        #            v = _i[1]
        #            post_dict['inputs'].update({key: v})
        #elif isinstance(post_data, dict):
        #    post_dict['inputs'].update(post_data)
        post_dict['inputs'].update(parse_qs(post_data))
        yaml_string = yaml.safe_dump(post_dict, default_flow_style=False)
        options.update({
            "plugins": {
                "vector_feed": {
                    "yaml_string": yaml_string
                }
            }
        })
        # pprint.pprint(options)
    else:
        options.update({
            "scope": {
                "page_limit": 1
            }
        })
    a.target(url, options)
    result = a.start_scan()
    if result:
        scan_id = result['id']
        print(scan_id)
        while True:
            time.sleep(5)
            status = a.get_status(scan_id)
            if status['status'] == 'done':
                issues = status['issues']
                if issues:
                    for i in issues:
                        _ = urllib.parse.urlparse(url)
                        if "default_inputs" in i['vector']:
                            default_inputs = "&".join(
                                [k + '=' + str(v) for k, v in i['vector']['default_inputs'].items()])
                        else:
                            default_inputs = ""
                        data = dict(
                            host=_.netloc,
                            vuln_url=url,
                            vuln_param=i['vector']['affected_input_name'],
                            default_inputs=default_inputs,
                            scheme=_.scheme,
                            path=_.path,
                            vuln_name=i['name'],
                            # page=i['page'],
                            request_raw=i['request']['headers_string'] + (
                                i['request']['effective_body'] or ""),
                            response_raw=i['response']['headers_string'] + (
                                i['response']['body'] or ""),
                            severity=i['severity'],
                        )
                        m.insert('vuln', data)
                break
