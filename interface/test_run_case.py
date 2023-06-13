# -*- coding: utf-8 -*-
import platform
import unittest

import requests
import ujson
from XTestRunner import HTMLTestRunner

from backends.settings import BASE_DIR

gl_config = None
gl_case_env = None


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """

    def __init__(self, methodName='runTest', param=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param


class TestInterFace(ParametrizedTestCase):
    s = requests.Session()
    v = {}  # 存储提取的临时变量

    @classmethod
    def tearDownClass(cls):
        TestInterFace.s.close()


def test_case(self):
    print(f"\n• 【用例】：\n{self.param['title']}")
    from interface.views import get_request_data, get_config, my_post_condition
    global gl_config, gl_case_env
    if gl_case_env:
        gl_config['variables'].update(TestInterFace.v)
    else:
        config = get_config(self.param.get('api_env'))
        gl_config['host'] = config['host']
        gl_config['variables'].update(config['variables'])
        gl_config['variables'].update(TestInterFace.v)
    params = get_request_data(self.param, gl_config)
    postConditionResult = []
    postCondition = params.pop('postCondition')
    try:
        res = TestInterFace.s.request(**params, stream=True, verify=False, timeout=3)
    except Exception as e:
        raise e
    res.raise_for_status()
    if res.json():
        print(
            f"• 【响应结果】：\nHTTP CODE: {res.status_code}\n{ujson.dumps(res.json(), ensure_ascii=False, sort_keys=True, indent=2, escape_forward_slashes=False)}")
    else:
        print(f"• 【响应结果】：\nHTTP CODE: {res.status_code}\n{res.text}")
    my_post_condition(res, postCondition, postConditionResult, variables=TestInterFace.v, option=2)


def run(case_env, config, apis_list, verbosity=1, name=None, title=None, description=None, tester=None):
    global gl_config, gl_case_env
    gl_case_env = case_env
    gl_config = config
    suite = unittest.TestSuite()
    for index, api in enumerate(apis_list, start=1):
        step_name = f"test_步骤{index}"
        setattr(TestInterFace, step_name, test_case)
        setattr(eval(f"TestInterFace.{step_name}"), "__doc__",
                u"%s" % api['title'])  # 给用例函数设置doc 注释  体现在报告里为小用例标题
        suite.addTest(TestInterFace(step_name, param=api))

    # 报告存放的文件夹
    report_path = BASE_DIR / f'interface/reports/{name}.html'
    if not report_path.exists():
        report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'wb') as f:
        runner = HTMLTestRunner(stream=f, verbosity=verbosity, title=title,
                                description=['类型：API', f'操作系统：{platform.platform()}',
                                             f'语言环境：Python{platform.python_version()}',
                                             f'创建人：{description[0]}'],
                                tester=tester,
                                language='zh-CN', rerun=2)
        runner.run(suite)
