import base64
import hashlib
import random
import re
import string
import time
import uuid


# 获取随机整数
def __random_int(_min: "Number", _max: "Number") -> "随机整数":
    if __is_number(_min) and __is_number(_max):
        return random.randint(int(_min), int(_max))
    else:
        return "请输入整数!"


# 获取当前秒时间戳
def __time_stamp(_time: "Time" = None, option: "Select" = None) -> "时间戳":
    if _time:
        timestamp = int(time.mktime(time.strptime(_time, '%Y-%m-%d %H:%M:%S')))
        return timestamp if option == 's' else timestamp * 1000
    else:
        return int(time.time()) if option == 's' else int(time.time() * 1000)


# 获取随机字符
def __random_string(length: "Number") -> "随机字符串":
    return ''.join(random.choices(string.digits + string.ascii_letters, k=length)) if length else "请输入字符串长度！"


# 验证手机号是否正确
def __is_mobile(mobile: "String") -> "判断手机号":
    return True if re.match(r'^1[3-9]\d{9}$', mobile) else False


# 验证数字
def __is_number(number: "String") -> "判断数字":
    return True if re.match(r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$', number) else False


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


if __name__ == '__main__':
    print(__random_mobile.__annotations__)
    print(__time_stamp('', 's'))
