#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
import base64
import hashlib
import hmac
import json
import os
import threading
import time
import urllib.parse

import requests

_print = print
mutex = threading.Lock()


def print(text, *args, **kw):
    with mutex:
        _print(text, *args, **kw)


push_config = {
    'CONSOLE': False,
    'DD_BOT_SECRET': '',
    'DD_BOT_TOKEN': '',
}

for k in push_config:
    if os.getenv(k):
        v = os.getenv(k)
        push_config[k] = v


def console(title: str, content: str) -> None:
    if str(push_config.get("CONSOLE")).lower() != "false":
        print(f"{title}\n\n{content}")


def dingding_bot(title: str, content: str) -> None:
    if not push_config.get("DD_BOT_SECRET") or not push_config.get("DD_BOT_TOKEN"):
        return
    print("钉钉机器人 服务启动")

    timestamp = str(round(time.time() * 1000))
    secret_enc = push_config.get("DD_BOT_SECRET").encode("utf-8")
    string_to_sign = "{}\n{}".format(timestamp, push_config.get("DD_BOT_SECRET"))
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(
        secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    url = f'https://oapi.dingtalk.com/robot/send?access_token={push_config.get("DD_BOT_TOKEN")}&timestamp={timestamp}&sign={sign}'
    headers = {"Content-Type": "application/json;charset=utf-8"}
    data = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
    response = requests.post(
        url=url, data=json.dumps(data), headers=headers, timeout=15
    ).json()

    if not response["errcode"]:
        print("钉钉机器人 推送成功！")
    else:
        print("钉钉机器人 推送失败！")


def add_notify_function():
    notify_function = []
    if str(push_config.get("CONSOLE")).lower() != "false":
        notify_function.append(console)
    if push_config.get("DD_BOT_TOKEN") and push_config.get("DD_BOT_SECRET"):
        notify_function.append(dingding_bot)
    if not notify_function:
        print(f"无推送渠道，请检查通知变量是否正确")
    return notify_function


def send(title: str, content: str, ignore_default_config: bool = False, **kwargs):
    if kwargs:
        global push_config
        if ignore_default_config:
            push_config = kwargs
        else:
            push_config.update(kwargs)

    if not content:
        print(f"{title} 推送内容为空！")
        return

    notify_function = add_notify_function()
    ts = [
        threading.Thread(target=mode, args=(title, content), name=mode.__name__)
        for mode in notify_function
    ]
    [t.start() for t in ts]
    [t.join() for t in ts]


def main():
    send("title", "content")


if __name__ == "__main__":
    main()