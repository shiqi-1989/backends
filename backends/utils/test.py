import os
import platform
import subprocess

cmd = "/Users/shiyanlei/Works/vue3-django/backends/venv/bin/xmind2testcase webtool 5503"
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
