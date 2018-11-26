import json
import os
import re

import datetime

import copy
import requests

import utils.vklib as vk
import utils.db_utils as db
import model as m
import consts as cnst
import config as cfg


def get_user_keyboard():
    k = cnst.KEYBOARD_USER
    k["buttons"][0][0]["action"]["label"] = db.get_first_btn()
    k["buttons"][0][0]["color"] = db.get_color_btn()
    return k


def get_user_enroll_btn():
    k = cnst.enroll_btn
    k[0]["action"]["label"] = db.get_first_btn()
    k[0]["color"] = db.get_color_btn()
    return k



class id_wrapper:
    def __init__(self):
        self.questions = db.get_quest_msgs()

    def get_db_id(self, vid):
        return self.questions[vid - 1].id

    def get_view_id(self, id):
        i = 1
        for q in self.questions:
            if q.id == id:
                return i
            i += 1

    def update(self):
        self.questions = db.get_quest_msgs()


ID_WRAPPER = id_wrapper()


def make_subs_file(uid):
    bot_followers = db.get_bot_followers()
    if len(bot_followers) == 0:
        text = 'В боте ещё нет подписчиков'
        vk.send_message(uid, text)
        return 'ok'
    filename = 'subs.csv'
    out = open(filename, 'a')
    text = 'ID; Имя; Статус; Подписан на рассылку\n'
    i = 0
    for x in bot_followers:
        i += 1
        text += '{};{};{};{}\n'.format(x.uid, x.name, x.status, x.mess_allowed)
        if i > 1000:
            out.write(text)
            text = ''
            i = 0
    out.write(text)
    out.close()
    res = vk.get_doc_upload_server1(uid)
    print(res)
    upload_url = res['response']['upload_url']
    files = {'file': open(filename, 'r')}
    response = requests.post(upload_url, files=files)
    result = response.json()
    print(result)
    r = vk.save_doc(result['file'])
    vk_doc_link = 'doc{!s}_{!s}'.format(r['response'][0]['owner_id'], r['response'][0]['id'])
    print(vk_doc_link)
    os.remove(filename)
    return vk_doc_link


def get_group_count(group_id=cfg.group_id):
    members_count = vk.get_count_group_followers(group_id)
    return int(members_count)


def del_uid_from_dict(uid, dict_):
    if uid in dict_:
        del dict_[uid]


def send_message_admins(info):
    admins = db.get_list_bot_admins()
    note = 'Примечания : {}'.format("\n".join(info.answers))
    vk.send_message_much(admins, cnst.NOTIFY_ADMIN.format(info.uid, info.name, info.email, info.number, note))


def send_message_admins_after_restart():
    admins = db.get_list_bot_admins()
    vk.send_message_much_keyboard(admins, cnst.MSG_SERVER_RESTARTED, get_user_keyboard())


def is_number_valid(number):
    match = re.fullmatch('^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,9}', number)
    if match:
        return True
    else:
        return False


def is_email_valid(email):
    match = re.fullmatch('[\w.-]+@\w+\.\w+', email)
    if match:
        return True
    else:
        return False


def new_user_or_not(uid, uname):
    if uname is None:
        uname = vk.get_user_name(uid)
    e = db.is_known_user(uid)
    if e:
        db.set_bot_follower_mess_allowed(uid, 1)
    else:
        db.add_bot_follower(uid, uname, status=cnst.USER_NOT_SUB_STATUS, msg_allowed=1)
        # vk.send_message_keyboard(uid, cnst.MSG_WELCOME_FOLLOWER.format(uname), cnst.KEYBOARD_USER)
    return not e


def parse_bcst(text):
    try:
        obj = m.BcstByTime()
        text_arr = text.split(' ', maxsplit=3)
        obj.start_date = datetime.datetime.strptime(text_arr[0], '%d.%m.%Y').date()
        obj.time = datetime.datetime.strptime(text_arr[1], '%H:%M').time()
        obj.repet_days = int(text_arr[2])
        return obj
    except BaseException:
        return None


def get_leave_reasons_as_str():
    reasons_list = db.get_leave_reasons()
    reasons_str = ''
    for r in reasons_list:
        reasons_str += r + '\n'
    return reasons_str


def save_leave_reasons(reasons_str):
    reasons = reasons_str.split('; ', 8)
    for r in reasons:
        db.add_leave_reason(r)
    return len(reasons)


def get_keyboard_from_list(list, def_btn=get_user_enroll_btn()):
    keyboard = copy.deepcopy(cnst.keyboard_pattern.copy())
    c = 0
    for i in list:
        if c == 7:
            break
        one_btns = copy.deepcopy(cnst.one_button_pattern)
        one_btns[0]['action']['label'] = i
        j = {"button": 'K'}
        one_btns[0]['action']['payload'] = json.dumps(j)
        keyboard['buttons'].append(one_btns)
        c += 1
    keyboard['buttons'].append(def_btn)
    return keyboard


def send_data_to_uon(data, uid):
    today = datetime.datetime.today()
    t = today.time()
    date_str = '{} {}:{}:{}'.format(today.date(), t.hour + cfg.time_zone_from_msk, t.minute, t.second)
    note = 'Примечания : {}'.format("\n".join(data.answers))
    payload = {
        'r_dat': date_str,
        'r_u_id': cfg.default_uon_admin_id,
        'u_name': data.name,
        'source': 'Бот вконтакте',
        'u_phone': data.number,
        'u_email': data.email,
        'u_social_vk': ('id' + str(uid)),
        'u_note': note
    }
    print(payload)
    url = 'https://api.u-on.ru/{}/lead/create.json'.format(cfg.uon_key)
    response = requests.post(url, data=payload)
    print(response)
    print(response.text)


def create_user_on_my_doc(data):
    name = data.name
    number = data.number
    email = data.email
    uid = data.uid
    if name is None:
        name = 'No name'
    if number is None:
        number = 'None'
    if email is None:
        email = 'None'
    if uid is None:
        uid = 'None'
    params = '{' \
            '"name":"' + name + '",' \
            '"tel":"' + number + '",' \
            '"email":"' + email + '",' \
            '"manager_id":"' + str(cfg.my_doc_manager_id) + '",' \
            '"vk":"id' + str(uid) + '"'\
            '}'
    payload = {
        'key': cfg.my_doc_key,
        'params': params
    }
    print(payload)
    url = 'https://{}.moidokumenti.ru/api/add-tourist-temp'.format(cfg.my_doc_addr)
    response = requests.post(url, params=payload)
    print(response)
    print(response.text)
    j = json.loads(response.text)
    id = j['tourist_temp_id']
    return id


def send_data_to_my_doc(data, uid):
    # today = datetime.datetime.today()
    # t = today.time()
    # d = today.date()
    # flightdate_from = d
    # flightdate_to = d.replace(year=d.year + 1)

    id = create_user_on_my_doc(data)

    note = 'Примечания - {}'.format("; ".join(data.answers))
    params = '{' \
             '"tourist_type":"tourist_temp",' \
             '"preorder_manager_id": ' + str(cfg.my_doc_manager_id) + ', ' \
             '"comment":"' + note + '",' \
            '"tourist_id":' + str(id)+ \
             '}'
    payload = {
        'key': cfg.my_doc_key,
        'params': params
    }
    print(payload)
    url = 'https://{}.moidokumenti.ru/api/create-preorder'.format(cfg.my_doc_addr)
    response = requests.post(url, params=payload)
    print(response)
    print(response.text)

d =m.EnrollInfo(1)
d.answers = ['1 jndtn', '2 ответ']
send_data_to_my_doc(d, 12)

def get_quest_msgs_as_str():
    quests = db.get_quest_msgs()
    str = ''
    if len(quests) == 0:
        str = '<Еще нет ни одного вопроса кроме вопросов о телефоне и email, которые есть всегда>'
    for q in quests:
        if len(q.answs) > 0:
            str += '(ID-{}) {} \n(Варианты ответа: {})\n\n'.format(ID_WRAPPER.get_view_id(q.id), q.quest, q.answs)
        else:
            str += '(ID-{}) {} \n\n'.format(ID_WRAPPER.get_view_id(q.id), q.quest)
    return str


def del_question(vid):
    db_id = ID_WRAPPER.get_db_id(vid)
    db.delete_quest_msg(db_id)
    ID_WRAPPER.update()


def add_quest_msg(quest, answs, vid=None):
    db_id = vid
    if vid is not None:
        db_id = ID_WRAPPER.get_db_id(vid)
    db.add_quest_msg(quest, answs, db_id)
    ID_WRAPPER.update()


def isint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def send_welcome_msg(uid, uname, keyboard):
    if uname is None:
        uname = vk.get_user_name(uid)
    msg = db.get_first_msg()
    vk.send_message_keyboard(uid, msg.format(uname), keyboard)


def emailing_to_all_subs_keyboard(uid, text):
    """
    Разослать текст всем подписчикам, кому возможно группы
    """
    count = 0
    arr = []
    users = db.get_bot_followers()
    for u in users:
        if u.is_msging_allowed():
            arr.append(u.uid)
            count += 1
        if len(arr) == 100:
            vk.send_message_much_keyboard(arr, text, get_user_keyboard())
            arr = []
    vk.send_message_much_keyboard(arr, text, get_user_keyboard())
    vk.send_message_keyboard(uid, cnst.MSG_BROADCAST_COMPLETED.format(count), cnst.KEYBOARD_ADMIN)
    return count

