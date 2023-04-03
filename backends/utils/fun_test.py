import random
import re
import string
import time


# 获取随机整数
def __get_random_int(_min: "Number", _max: "Number"):
    return random.randint(_min, _max)


# 获取当前秒时间戳
def __get_timestamp(_time: "Time" = None, option: "Select" = None):
    if _time:
        timestamp = int(time.mktime(time.strptime(_time, '%Y-%m-%d %H:%M:%S')))
        return timestamp if option == 's' else timestamp * 1000
    else:
        return int(time.time()) if option == 's' else int(time.time() * 1000)


# 获取随机字符
def __get_random_string(length: "Number"):
    return ''.join(random.choices(string.digits + string.ascii_letters, k=length))


# 验证手机号是否正确
def __is_mobile(mobile: "String"):
    return True if re.match(r'^1[3-9]\d{9}$', mobile) else False


# 验证数字
def __is_number(number: "String"):
    return True if re.match(r'^[0-9]*$', number) else False


# 获取随机手机号
def __get_random_mobile():
    return "1" + random.choice("3456789") + ''.join(random.sample(string.digits, k=9))


if __name__ == '__main__':
    print(__get_random_int.__annotations__)
