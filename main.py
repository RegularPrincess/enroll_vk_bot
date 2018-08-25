#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
from flask import json
from flask import request
import logging as log

import config
import service as s


token = config.token
confirmation_token = config.confirmation_token
secret_key = config.secret_key
group_id = config.group_id
admin_id = config.admin_id
admin_name = config.admin_name
db_name = config.db_name
bot_name = config.bot_name
vk_api_url = config.vk_api_url


app = Flask(__name__)


@app.route(rule='/', methods=['GET'])
def debug():
    return "hello world"


@app.route(rule='/{0}'.format(bot_name), methods=['POST'])
def processing():
    print('Пришел пост запрос')
    data = json.loads(request.data)

    if 'secret' not in data.keys():
        print('Not vk')
        return 'Not VK.'
    elif not data['secret'] == secret_key:
        print(data['secret'] + "  token не подходит")
        return 'Bad query.'
    if data['type'] == 'confirmation':
        print("Группа привязана!")
        return confirmation_token
    elif data['type'] == 'group_join':
        uid = data['object']['user_id']
        answer = s.group_join(uid)
        return answer
    elif data['type'] == 'message_new':
        uid = data['object']['from_id']
        text = data['object']['text']
        answer = s.message_processing(uid, text)
        return answer
    elif data['type'] == 'group_leave':
        uid = data['object']['user_id']
        answer = s.group_leave(uid)
        return answer
    elif data['type'] == 'message_allow':
        uid = data['object']['user_id']
        answer = s.message_allow(uid)
        return answer
    elif data['type'] == 'message_deny':
        uid = data['object']['user_id']
        answer = s.message_deny(uid)
        return answer
    return 'ok'


def main(argv):
    print ("Старт")
    port = int(argv[1])
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    import sys
    main(sys.argv[0:])
