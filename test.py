import os
import subprocess

env = 1
cmd_list = [f"cd D:/ProJect/vue3-django/backends/venv/Scripts", "./xmind2testcase webtool 5501"] if env == 1 else [
    "xmind2testcase webtool 5501"]

p = subprocess.Popen("xmind2testcase webtool 5509",
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.PIPE)

print(1111111111111111)
