import datetime

from rediscluster import RedisCluster


def get_msg(env, phone, config):
    config = {
        "alpha": {
            "startup_nodes": [
                {
                    "host": "172.20.0.26",
                    "port": 6679
                },
                {
                    "host": "172.20.0.27",
                    "port": 6679
                },
                {
                    "host": "172.20.0.28",
                    "port": 6679
                }
            ],
            "password": ""
        },
        "release": {
            "startup_nodes":
                [
                    {
                        "host": "htzx-cluster.redis.rds.aliyuncs.com",
                        "port": 6379
                    }
                ],
            "password": "lbQ7$c5No^HLsvhV"
        }
    }
    print(config["alpha"])
    with RedisCluster(**config, decode_responses=True) as red:
        msg = "没有查询到！"
        key = f"captcha_{phone}"
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        ttl_time = red.ttl(key)
        if red.exists(key) == 1:
            text = red.get(key)
            msg = f"{env} | phone: {phone}, 验证码: {text}, {ttl_time}"
        print(msg)
        return msg


# 获取验证码

if __name__ == '__main__':
    get_msg('release', '13716610001', "")
