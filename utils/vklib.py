#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests
import config
import logging as log


api_ver = config.api_ver


def is_messages_allowed(uid, group_id=config.group_id):
    data = {
        'group_id': group_id,
        'user_id': uid,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'messages.isMessagesFromGroupAllowed', data=data)
    try:
        d = json.loads(res.text)['response']['is_allowed']
        return d == 1
    except Exception:
        print(res.text)
        return False


def send_message(user_id, text):
    """
    Send VK message
    """
    data = {
        'message': text,
        'user_id': user_id,
        'access_token': config.token,
        'v': api_ver
    }
    r = requests.post(config.vk_api_url + 'messages.send', data=data)
    print(r)


def send_message_keyboard(user_id, text, keyboard):
    """
    Send VK message with keyboard. Keyboard - json dictionary
    """
    data = {
        'message': text,
        'user_id': user_id,
        'access_token': config.token,
        'keyboard': json.dumps(keyboard, ensure_ascii=False),
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'messages.send', data=data)
    print(res)


def get_group_memebers(group_id, offset=0, count=1000):
    """
    Get group members
    """
    data = {
        'group_id': group_id,
        'offset': offset,
        'count': count,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'groups.getMembers', data=data)
    try:
        return json.loads(res.text)['response']['items']
    except Exception:
        print(res.text)
        return []


def get_user_name(uid):
    """
    Получить полное имя пользователя
    """
    data = {
        'user_ids': uid,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'users.get', data=data)
    try:
        d = json.loads(res.text)['response'][0]
        return d['first_name'] + ' ' + d['last_name']
    except Exception:
        print(res.text)
        return ''


def get_count_group_followers(group_id):
    """
    Получить количество подписчиков группы
    """
    data = {
        'group_id': group_id,
        'fields': 'members_count,',
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'groups.getById', data=data)
    try:
        d = json.loads(res.text)['response'][0]
        return int(d['members_count'])
    except Exception:
        print(res.text)
        return 0


def send_message_much(user_ids, text):
    """
    Отправить сообщения многим пользователям за один запрос
    """
    d = str(user_ids).strip('[]').replace(' ', '')
    print(d)
    data = {
        'message': text,
        'user_ids': d,
        'access_token': config.token,
        'v': api_ver
    }
    answ = requests.post(config.vk_api_url + 'messages.send', data=data)
    print(answ)


def send_message_much_keyboard(user_ids, text, keyboard):
    """
    Отправить сообщения с клавиатурой многим пользователям за один запрос
    """
    d = str(user_ids).strip('[]').replace(' ', '')
    print(d)
    data = {
        'message': text,
        'user_ids': d,
        'access_token': config.token,
        'keyboard': json.dumps(keyboard, ensure_ascii=False),
        'v': api_ver
    }
    answ = requests.post(config.vk_api_url + 'messages.send', data=data)
    print(answ)


def get_messages_upload_server(peer_id):
    """
    Получить сервер ВК для загрузки фото в ЛС
    """
    data = {
        'peer_id': peer_id,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'photos.getMessagesUploadServer', data=data)
    return res.json()


def save_messages_photo(photo, server, hash):
    """
    Сохраняет фотографию после успешной загрузки на URI
    """
    data = {
        'photo': photo,
        'server': server,
        'hash': hash,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'photos.saveMessagesPhoto', data=data)
    return res.json()


def send_message_with_photo(user_id, text, photo):
    """
    Отправить сообщение с фото
    :param photo: строка вида photoOWNERID_PHOTOID
    """
    data = {
        'message': text,
        'user_id': user_id,
        'attachment': photo,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'messages.send', data=data)
    print(res.text)


def get_doc_upload_server1(peer_id):
    """
    Получить сервер ВК для загрузки фото в ЛС
    """
    data = {
        'peer_id': peer_id,
        'access_token': config.token,
        'v': '5.78'
    }
    res = requests.post(config.vk_api_url + 'docs.getMessagesUploadServer', data=data)
    return res.json()


def save_doc(file):
    """
    Сохранить документ ВК
    """
    data = {
        'file': file,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'docs.save', data=data)
    return res.json()


def send_message_doc(user_id, text, doc):
    """
    Отправить сообщение с документом
    """
    data = {
        'message': text,
        'user_id': user_id,
        'attachment': doc,
        'access_token': config.token,
        'v': api_ver
    }
    requests.post(config.vk_api_url + 'messages.send', data=data)


def parse_24_subs(ids):
    code = 'var ids = ' + str(ids) + '''
    ;var i = 0;        
        var data = [];
        var users = API.users.get({"user_ids":ids});
        while(i < ids.length){
            data.push(ids[i]);
            data.push(users[i].first_name + " " + users[i].last_name);
            var allow = API.messages.isMessagesFromGroupAllowed({"group_id": ''' + str(config.group_id) + ''', "user_id":ids[i]});
            data.push(allow.is_allowed);
            i = i + 1;
        }
        return data;'''
    data = {
        'code': code,
        'access_token': config.token,
        'v': api_ver
    }
    res = requests.post(config.vk_api_url + 'execute', data=data)
    return res
