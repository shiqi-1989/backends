import re
from backends.utils import fun_test

config = {
    'sho': {'dddd': 123}
}
#
#
# def get_func_variable(exp):
#     fun, variable = exp.strip().rsplit(",", 1)
#     if variable:
#         print(f"变量名是： {variable}")
#         config[variable.strip()] = 'shiyanlei'
#     print(config)
#
#
# aa = None
# print(config.get('shi', '') + '123')
# config.get('auth').update({'a': 123})
# print(config.get('auth'))
# print(config)
aa = config.get('sho')
aa['auth'] = 1111
print(config)
