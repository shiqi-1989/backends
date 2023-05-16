import asyncio
import os
import platform
import re
import subprocess
import sys
import time
import datetime

from rediscluster import RedisCluster
import chardet
import httpx
from jsonpath import jsonpath
from jmespath import search
from orjson import orjson
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backends.settings import FILES_ROOT, MY_HOST, MY_PORT, BASE_DIR
from interface.models import Config, Api, Case, Report
from interface.test_run_case import run
from . import fun_test
from pprint import pprint


#  获取simple jwt token
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh), str(refresh.access_token)


def get_now_time():
    """获取当前时间"""
    from django.utils import timezone
    # 返回时间格式的字符串
    now_time = timezone.now()
    now_time_str = now_time.strftime("%Y.%m.%d %H:%M:%S")
    print(now_time_str)

    # 返回datetime格式的时间
    # now_time = timezone.now().astimezone(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
    # now = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')
    return now_time_str


def get_user_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
        print(f"真实ip：{ip}")
    else:
        ip = request.META.get('REMOTE_ADDR')
        print(f"代理ip：{ip}")

    return ip


def run_cmd(cmd):
    sh = subprocess.Popen(cmd,
                          shell=True,
                          stdin=None,
                          stdout=open(os.devnull, 'wb'),
                          stderr=open(os.devnull, 'wb'))
    # sh = subprocess.Popen(cmd,
    #                       shell=True,
    #                       stdin=None,
    #                       stdout=None,
    #                       stderr=None)
    return sh


def get_manufacturer(device):
    print(111111)
    print(device)
    sh = run_cmd(f'adb -s {device} shell getprop ro.product.manufacturer')
    sh2 = run_cmd(f'adb -s {device} shell getprop ro.product.model')
    manufacturer = read_sh(sh).replace(' ', '')
    model = read_sh(sh2).replace(' ', '-')
    return f'{manufacturer}_{model}'


def read_sh(sh):
    content = sh.stdout.read()
    sh.stdout.close()
    msg = None
    if content:
        encoding = chardet.detect(content)['encoding']
        msg = str(content, encoding=encoding).strip()
    print(msg)
    return msg


def get_dict(obj):
    new_dict = {}
    modified = ['If-None-Match', 'If-Modified-Since', 'Expires', 'Last-Modified']
    for i in obj:
        if i['selected'] and i['name']:
            if i['name'] in modified:
                new_dict.update({i['name']: ""})
            else:
                new_dict.update({i['name']: i['value']})
    return new_dict


def get_hosts(obj):
    hosts = []
    for i in obj:
        if i['selected'] and i['name']:
            hosts.append(i['value'])
    return hosts


def get_config(env):
    _config = {
        "host": "",
        "variables": {}
    }
    if env:
        config = Config.objects.get(id=env)
        _config['host'] = get_hosts(config.hosts)[0]
        _config['variables'] = get_dict(config.variables)
    return _config


def json_str(dic):
    return orjson.dumps(dic, option=orjson.OPT_INDENT_2).decode()


def get_request_data(data, config=None):
    # pprint(data)
    if config:
        variables = config.get('variables')
    else:
        variables = {}

    def _replace(match):
        content = match.group(1)
        if content.startswith("__"):
            func, variable = get_func_variable(content)
            func = func.replace("\\", "")
            result = get_func_result(func)
            if variable:
                variables[variable] = result
            return result
        elif variables:
            return str(variables.get(content))

    data_str = orjson.dumps(data).decode()
    new_str = re.sub(r'\${(.*?)}', _replace, data_str)
    new_data = orjson.loads(new_str)
    if config: new_data['url'] = config.get('host') + new_data['url']

    # if config:
    #     data_str = orjson.dumps(data).decode()
    #     new_str = re.sub(r'\${(.*?)}', _replace, data_str)
    #     new_data = orjson.loads(new_str)
    #     new_data['url'] = config.get('host') + new_data['url']
    # else:
    #     new_data = data
    print(f"• 【请求url】：\n{new_data['method']} {new_data['url']}")
    params = get_dict(new_data['queryData'])
    print(
        f"• 【请求params】：\n{json_str(params)}")
    headers = get_dict(new_data['headersData'])
    print(
        f"• 【请求header】：\n{json_str(headers)}")
    cookies = get_dict(new_data['cookies'])
    print(
        f"• 【请求cookies】：\n{json_str(cookies)}")
    print(f"• 【请求body】：")
    data, files = {}, {}
    json_data = None
    if new_data['bodyType'] == 'x-www-form-urlencoded':
        data = get_dict(new_data['formUrlencodedData'])
        print(f"{json_str(data)}")
    elif new_data['bodyType'] == 'raw':
        json_data = orjson.loads(new_data['rawData']['text'])
        print(json_str(json_data))
    elif new_data['bodyType'] == 'form-data':
        if headers.get('Content-Type'):
            del headers['Content-Type']
        # data = {}
        # files = {}
        # files = []
        # for i in new_data['formData']:
        #     if i['name']:
        #         if i['type'] == 'file':
        #             for file in i['fileList']:
        #                 name = i['name']
        #                 file_name = file['response']['data']['name']
        #                 _type = file['raw']['type']
        #                 files.append((name, (file_name, open(FILES_ROOT / file_name, 'rb'), _type)))
        #         else:
        #             data[i['name']] = i['value']
        for i in new_data['formData']:
            if i['name']:
                if i['type'] == 'file':
                    for file in i['fileList']:
                        name = i['name']
                        file_name = file['response']['data']['name']
                        file_path = file['response']['data']['file'].rsplit("/", 1)[1]
                        print('-----------------------')
                        print(FILES_ROOT / file_path)
                        print('-----------------------')
                        _type = file['raw']['type']
                        # with open(FILES_ROOT / file_name, 'rb') as f:
                        #     files[name] = (file_name, f.read(), _type)
                        files[name] = (file_name, open(FILES_ROOT / file_path, 'rb'), _type)
                else:
                    files[i['name']] = (None, i['value'])
        if files:
            print(files)
    return {
        "method": new_data['method'],
        "url": new_data['url'],
        "headers": headers,
        "params": params,
        "cookies": cookies,
        "data": data,
        "json": json_data,
        "files": files,
        "postCondition": new_data['postCondition']
    }


def run_case(case_id, user=None):
    msg_info = {
        "report": None,
        "msg": "成功",
        "code": 200
    }
    case_info = Case.objects.get(id=case_id)
    obj_list = Api.objects.filter(pk__in=case_info.steps).values('id', 'title', 'method', 'url', 'bodyType',
                                                                 'queryData',
                                                                 'headersData', 'cookies', 'formData',
                                                                 'formUrlencodedData',
                                                                 'rawData', 'postCondition', 'api_env')
    obj_list = sorted(obj_list, key=lambda x: case_info.steps.index(x['id']))
    if not obj_list:
        msg_info['msg'] = '无可执行的有效步骤！'
        msg_info['code'] = 100
        return msg_info
    filters = {
        "project": case_info.project_id,
        "type": 0
    }
    g_config = get_dict(Config.objects.filter(**filters).first().variables)
    config = get_config(case_info.case_env)
    g_config.update(config['variables'])
    config['variables'] = g_config
    print(config)
    report_name = f"{case_info.title}-{int(time.time() * 1000)}"
    run(case_info.case_env, config, obj_list, name=report_name, title=case_info.title,
        description=[case_info.creator, case_info.info],
        tester=user)
    msg_info['report'] = f"http://{MY_HOST}:{MY_PORT}/interface/report/get_detail?title={report_name}"
    Report.objects.create(title=report_name, case=case_info, creator=user)
    return msg_info


def my_assert(option, msg, actual, way, expected=None):
    # print(actual)
    # print(type(actual).__name__)
    #
    # print(expected)
    # print(type(expected).__name__)
    # msg["name"] = f"断言「{msg['name']}」:"
    try:
        if way == 0:
            assert actual == expected, f"实际:{actual}({type(actual).__name__}), 预期:{expected}({type(expected).__name__})"
            msg["content"] = f"实际:{actual}({type(actual).__name__}), 预期:{expected}({type(expected).__name__})"
            print(f"实际:{actual}({type(actual).__name__}), 预期:{expected}({type(expected).__name__})")
        if way == 1:
            assert actual != expected, f"实际:{actual}({type(actual).__name__}), 预期:{expected}({type(expected).__name__})"
            msg["content"] = f"实际:{actual}({type(actual).__name__}), 预期:{expected}({type(expected).__name__})"
        if way == 2:
            assert actual, f"实际:{actual}({type(actual).__name__}), 预期: 存在"
            msg["content"] = f"实际:{actual}({type(actual).__name__}), 预期: 存在"
        if way == 3:
            assert not actual, f"实际:{actual}({type(actual).__name__}), 预期: 不存在"
            msg["content"] = f"实际:{actual}({type(actual).__name__}), 预期: 不存在"
        if way == 4:
            assert actual in expected, f"实际:{actual}({type(actual).__name__}) NOT IN 预期: {expected}({type(expected).__name__})"
            msg["content"] = f"实际:{actual}({type(actual).__name__}) IN 预期: {expected}({type(expected).__name__})"
        if way == 5:
            assert actual not in expected, f"实际:{actual}({type(actual).__name__}) IN 预期: {expected}({type(expected).__name__})"
            msg[
                "content"] = f"实际:{actual}({type(actual).__name__}) NOT IN 预期: {expected}({type(expected).__name__})"
        if way == 6:
            assert actual is None, f"实际:{actual}({type(actual).__name__}) Is Not None"
            msg["content"] = f"实际:{actual}({type(actual).__name__}) Is None"
        if way == 7:
            assert actual is not None, f"实际:{actual}({type(actual).__name__}) Is None"
            msg["content"] = f"实际:{actual}({type(actual).__name__}) Is Not None"
        # print("断言通过")
        # print(msg)
    except Exception as e:
        msg['content'] = f"AssertionError: {e}"
        msg['status'] = False
        # print(f"AssertionError：{e}")
        print("断言失败！")
        if option:
            raise


def my_post_condition(res, postCondition, postConditionResult, variables=None, option=None, config_id=None):
    print("后置操作".center(60, '*'))
    if variables is None:
        variables = {}
    for item in postCondition:
        if item['postConditionSwitch']:
            expression = item['expression']
            msg = {
                "status": True,
                "name": item["name"],
                "content": ""
            }
            if item['type'] == 0:
                msg["name"] = f"断言「{item['name']}」:"
                print("• 【断言】:")
            if item['type'] == 1:
                msg["name"] = f"提取变量「{item['name']}」:"
                print("• 【提取变量】:")
            # 正则提取
            if item['resMetaData'] == 0:
                # print("正则提取")
                reg = re.compile(r"%s" % expression)
                actual_list = reg.findall(res.text)
                # print(f"正则结果： {actual_list}")
                if actual_list:
                    actual = actual_list[item['expressionIndex']]
                    # 断言
                    if item['type'] == 0:
                        expected = item['assert']['expected']
                        # print(f"预期结果值{expected} 类型 {type(expected).__name__}")
                        try:
                            expected = eval(f"{item['assert']['expectedType']}({repr(expected)})")
                        except Exception as e:
                            print(e.__str__())
                            expected = None
                        my_assert(option, msg, actual, item['assert']['way'], expected)
                    # 提取
                    if item['type'] == 1:
                        variables[item['name']] = actual
                        msg["content"] = f"{actual}"
                        print(f"{item['name']}:{actual}")
                else:
                    msg["status"] = False
                    msg["content"] = f"正则提取 {actual_list}"
                    print(f"正则提取失败: {expression}")
                    postConditionResult.append(msg)
                    continue

            #  json提取
            if item['resMetaData'] == 1:
                # print("Json提取")
                # actual = jsonpath(res.json(), expression)
                actual = search(expression, res.json())
                if not actual:
                    # msg["name"] = f"提取变量「{item['name']}」:"
                    msg["status"] = False
                    msg["content"] = f"Json提取{actual}"
                    print(f"Json提取失败：{expression}")
                    postConditionResult.append(msg)
                    continue
                if item['continueExtract']['is'] == 1:
                    separator = item['continueExtract']['separator']
                    index = item['continueExtract']['index']
                    try:
                        actual = re.split(f'[{separator}]', actual)[index]
                    except Exception as e:
                        print(f"Json提取失败：{e.__str__()}")
                        # msg["name"] = f"提取变量「{item['name']}」:"
                        msg["status"] = False
                        msg["content"] = f"继续提取变量值：{e.__str__()}"
                        postConditionResult.append(msg)
                        continue

                # print("最终结果")
                # print(actual)
                # 断言
                if item['type'] == 0:
                    # print(f"预期结果类型{item['assert']['expectedType']}")
                    expected = item['assert']['expected']
                    # print(f"预期结果值{expected} 类型 {type(expected).__name__}")
                    try:
                        expected = eval(f"{item['assert']['expectedType']}({repr(expected)})")
                    except Exception as e:
                        print(e.__str__())
                        expected = None
                    my_assert(option, msg, actual, item['assert']['way'], expected)
                # 提取
                if item['type'] == 1:
                    variables[item['name']] = actual
                    print(f"{item['name']}:{actual}")
                    # msg["name"] = f"提取变量「{item['name']}」:"
                    msg["content"] = f"{actual}"
                    if item.get('config'):
                        config_id = item['config']
                    if config_id:
                        _c = Config.objects.get(id=config_id)
                        _c_list = _c.variables
                        on_off = True
                        for i in _c_list:
                            if i['name'] == item['name']:
                                i['value'] = actual
                                on_off = False
                        if on_off:
                            _c_list.append({
                                "name": item['name'],
                                "value": actual,
                                "selected": True
                            })
                        _c.variables = _c_list
                        _c.is_active = True
                        _c.save()
            postConditionResult.append(msg)


def get_func_variable(exp):
    return exp.strip().rsplit(",", 1)


def get_func_result(exp):
    # print(exp)
    func = re.findall(r'(__.*?)\(', exp)[0]
    # print(func)
    params = re.findall(r'\((.+)\)', exp)
    # print(params)
    params = params[0].split(',') if params else params
    # print(params)
    return getattr(fun_test, func)(*params)


# 异步函数
async def req(client, params, obj_id):
    # _status, res = None, None
    # start_time = int(round(time.time() * 1000))
    res = await client.request(**params)
    # try:
    #     res = await client.request(**params)
    #     my_post_condition(res, postCondition, postConditionResult)
    #     try:
    #         res_content = res.json()
    #     except:
    #         res_content = res.text
    #     response = {
    #         "data": res_content,
    #         "postConditionResult": postConditionResult,
    #         "status": res.status_code,
    #         "startTime": start_time,
    #         "duration": int(res.elapsed.total_seconds() * 1000)
    #     }
    # except Exception as e:
    #     print(e.__str__())
    #     err = "请求异常！"
    #     if e.__str__():
    #         err = e.__str__()
    #     if res:
    #         duration = int(res.elapsed.total_seconds() * 1000)
    #         _status = res.status_code
    #     else:
    #         duration = int(time.time() * 1000) - start_time
    #         _status = status.HTTP_500_INTERNAL_SERVER_ERROR
    #     response = {
    #         "data": err,
    #         "postConditionResult": postConditionResult,
    #         "status": _status,
    #         "startTime": start_time,
    #         "duration": duration
    #     }
    # finally:
    #     api = Api.objects.filter(id=obj_id)
    #     api.update(response=response)
    api = Api.objects.filter(id=obj_id)
    api.update(status=res.status_code)


# 异步调用 异步函数
async def main(obj_list):
    task_list = []  # 任务列表
    async with httpx.AsyncClient() as client:
        for obj in obj_list:
            if obj.get('api_env'):
                config = get_config(obj.get('api_env'))
            params = get_request_data(obj)
            res = req(client, params, obj['id'])
            task = asyncio.create_task(res)  # 创建任务
            task_list.append(task)
        await asyncio.wait(task_list)  # 收集任务


# 启动xmind2testcase
def xmind2testcase_start(env=1):
    """
    启动xmind2testcase
    :param env: 1-虚拟环境；2-系统环境
    """
    if platform.system() == "Windows":
        cmd = f"{BASE_DIR}\\venv\\Scripts\\xmind2testcase webtool 5501" if env == 1 else "xmind2testcase webtool 5501"
    else:
        cmd = f"{BASE_DIR}/venv/bin/xmind2testcase webtool 5501" if env == 1 else "xmind2testcase webtool 5501"
    run_cmd(cmd)


# 定义一个开关函数
def print_switch(option):
    option = True
    if option:
        sys.stdout = sys.__stdout__
    else:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')


# 获取验证码
def get_msg(env, phone, config):
    with RedisCluster(**config, decode_responses=True) as red:
        msg = "没有查询到！"
        key = f"captcha_{phone}"
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        ttl_time = red.ttl(key)
        if red.exists(key) == 1:
            text = red.get(key)
            msg = f"{env} | phone: {phone}, 验证码: {text}, {ttl_time}"
        print(msg)
        return msg


def get_request_info(request):
    text = ""
    request = request.__dict__
    for key in request:
        if key == 'headers':
            for item, value in request['headers'].items():
                text += f"{item}".ljust(20) + f"  {value}\n"
        else:
            text += f"{key}".ljust(20) + f"  {request[key]}\n"
    return text


# 获取验证码

if __name__ == '__main__':
    # get_msg('alpha', '13716610001', "")
    get_func_result("__random_mobile()")
