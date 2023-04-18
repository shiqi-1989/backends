import re


def get_func_result(exp):
    # print(exp)
    func = re.findall(r'(__.*?)\(', exp)[0]
    # print(func)
    params = re.findall(r'\((.+)\)', exp)
    # print(params)
    params = params[0].split(',') if params else params
    # print(params)


if __name__ == '__main__':
    # get_msg('alpha', '13716610001', "")
    get_func_result("__random_mobile(a,b)")
