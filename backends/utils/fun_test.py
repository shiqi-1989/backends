import base64
import datetime
import hashlib
import random
import re
import string
import time
import uuid


# 获取随机整数
def __random_int(_min: "Number", _max: "Number") -> "随机整数":
    if __is_number(_min) and __is_number(_max):
        return str(random.randint(int(_min), int(_max)))
    else:
        return "请输入整数!"


# 获取当前秒时间戳
def __time_stamp(_time: "Time" = None, option: "Select" = None) -> "时间戳":
    if _time:
        timestamp = int(time.mktime(time.strptime(_time, '%Y-%m-%d %H:%M:%S')))
        return timestamp if option == 's' else timestamp * 1000
    else:
        return str(int(time.time()) if option == 's' else int(time.time() * 1000))


def __timestamp_to_str(timestamp_str: "String") -> "时间戳转时间":
    timestamp = int(timestamp_str) if len(timestamp_str) == 10 else int(timestamp_str) / 1000
    datetime_obj = datetime.datetime.fromtimestamp(timestamp)
    return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')


# 获取随机字符
def __random_string(length: "Number") -> "随机字符串":
    if __is_number(length):
        return ''.join(random.choices(string.digits + string.ascii_letters, k=int(length))) if length else "请输入字符串长度！"
    else:
        return "请输入正整数!"


# 验证手机号是否正确
def __is_mobile(mobile: "String") -> "判断手机号":
    return "true" if re.match(r'^1[3-9]\d{9}$', mobile) else "false"


# 验证数字
def __is_number(number: "String") -> "判断数字":
    return "true" if re.match(r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$', number) else "false"


# 获取随机手机号
def __random_mobile() -> "随机手机号":
    return "1" + random.choice("3456789") + ''.join(random.sample(string.digits, k=9))


# MD5 加密
def __md5(string: "String") -> "MD5加密":
    return hashlib.md5(string.encode('utf-8')).hexdigest()


# BASE64加密
def __base64(string: "String") -> "BASE64加密":
    return base64.b64encode(string.encode('utf-8')).decode('utf-8')


# BASE64解密
def __base64_decode(string: "String") -> "BASE64解密":
    return base64.b64decode(string.encode('utf-8')).decode('utf-8')


# 获取 UUID
def __uuid() -> "UUID":
    return str(uuid.uuid1())


# 时间戳计算
def __time_calculator(_time: "Time" = None, days: "Number" = None) -> "时间计算器":
    res = datetime.datetime.fromisoformat(_time) if _time else datetime.datetime.now().replace(microsecond=0)
    if days and __is_number(days):
        lai = res + datetime.timedelta(days=int(days))
    elif days:
        lai = "days 请输入整数"
    else:
        lai = res + datetime.timedelta(days=0)
    return lai.strftime("%Y-%m-%d %X")


if __name__ == '__main__':
    # print(__random_mobile.__annotations__)
    # print(__timestamp_to_str("1681458301571"))
    params = ['', '']
    __time_calculator(*params)
