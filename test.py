import datetime

# res = datetime.datetime.now().replace(microsecond=0)
# print(res)
# print(type(res))

# res = "2023-04-16 12:03:21"
res = datetime.datetime.now().replace(microsecond=0)
# res = datetime.datetime.fromisoformat(res)
print(res)
print(type(res))
lai = res + datetime.timedelta(days=0)
print(lai)
print(type(lai))
