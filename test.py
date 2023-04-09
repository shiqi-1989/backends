import re
import random

from backends.utils import fun_test


#  定义函数 获取函数结果
def get_func_result(exp):
    func = re.findall(r'(__.*?)\(', exp)[0]
    print(func)
    params = re.findall(r'\((.*?)\)', exp)[0].split(',')
    print(params)
    return getattr(fun_test, func)(*params)


print(random.randint(-12, 12))
print(int('-7'))

print('-7'.isalnum())
print('-7'.isdecimal())
print('-7'.isnumeric())
