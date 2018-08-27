import os
import config as cfg
from threading import Thread
import utils.db_utils as db
import utils.vklib as vk
import utils.service_utils as us
import consts as cnst
import json
import requests
import time
from datetime import datetime, date, timedelta
import model as m
import utils.service_utils as su


class ThreadManager:
    def __init__(self):
        self.bcst_threads = []

    def run_brdcst_shedule(self):
        bcst = db.get_bcsts_by_time()
        self.bcst_threads = []
        for b in bcst:
            self.bcst_threads.append(ThreadBrdcst(b))
        for bt in self.bcst_threads:
            bt.start()

    def add_brcst_thread(self, bcst):
        db.add_bcst(bcst)
        self.run_brdcst_shedule()

    def delete_brcst(self, id):
        db.delete_bcst(id)
        self.run_brdcst_shedule()


class ThreadBrdcst(Thread):
    def __init__(self, bcst):
        """Инициализация потока"""
        Thread.__init__(self)
        self.bcst = bcst

    def run(self):
        day = self.bcst.start_date
        time_ = self.bcst.time
        plane = datetime.combine(day, time_)
        wait_time = 0
        while True:
            now = datetime.today()
            while plane < now:
                plane += timedelta(days=self.bcst.repet_days)
            if plane >= now:
                wait_time = (plane - now).total_seconds()
            time.sleep(wait_time)
            us.emailing_to_all_subs_keyboard(self.bcst.msg)
            time.sleep(61)

#
# class ThreadParseGroup(Thread):
#     def __init__(self, uid, group_id=cfg.group_id):
#         """Инициализация потока"""
#         Thread.__init__(self)
#         self.uid = uid
#         self.group_id = group_id
#
#     def run(self):
#


class ThreadSubs(Thread):
    def __init__(self, uid, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.group_id = group_id

    def run(self):
        vk_doc_link = su.make_subs_file(self.uid)
        vk.send_message_doc(self.uid, cnst.MSG_SUBS, vk_doc_link)


class ThreadParse24Subs(Thread):
    def __init__(self, uids, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uids = uids
        self.group_id = group_id

    def run(self):
        res = vk.parse_24_subs(self.uids).content["response"]
        for i in range(0, len(res)//3):
            c = i*3
            db.add_bot_follower(uid=res[c], name=res[c+1], msg_allowed=[c+2])


class ThreadParseGroup(Thread):
    def __init__(self, uid, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.group_id = group_id

    def run(self):
        members_count = su.get_group_count()
        msg = cnst.MSG_MEMBERS_COUNT.format(members_count)
        vk.send_message(self.uid, msg + '\n ' + cnst.MSG_PLEASE_STAND_BY)
        follower_list = db.get_bot_followers(only_id=True)
        iterations = members_count // 1000 + 1
        users_added = 0
        for x in range(iterations):
            users = vk.get_group_memebers(self.group_id, offset=x * 1000, count=1000)
            for_parse = []
            thread_count = 0
            for user_id in users:
                try:
                    if not user_id in follower_list:
                        for_parse.append(user_id)
                    if len(for_parse) == 24:
                        t = ThreadParse24Subs(for_parse)
                        t.start()
                        for_parse = []
                        thread_count += 1
                        if thread_count > 12:
                            time.sleep(2)
                            thread_count = 0
                except Exception as e:
                    print(e)
                    pass
            if len(for_parse) > 0:
                t = ThreadParse24Subs(for_parse)
                t.start()

        msg = cnst.MSG_ADDED_COUNT
        vk.send_message(self.uid, msg)


class ThreadSendMsgWelcome(Thread):
    def __init__(self, uid, uname, keyboard, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.uname = uname
        self.keyboard = keyboard
        self.group_id = group_id

    def run(self):
        su.send_welcome_msg(self.uid, self.uname, self.keyboard)


class ThreadSendMsg(Thread):
    def __init__(self, uid, msg, keyboard=None, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.msg = msg
        self.keyboard = keyboard
        self.group_id = group_id

    def run(self):
        if self.keyboard is None:
            vk.send_message(self.uid, self.msg)
        else:
            vk.send_message_keyboard(self.uid, self.msg, self.keyboard)


class ThreadNewUserOrNote(Thread):
    def __init__(self, uid, uname):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.uname = uname

    def run(self):
        us.new_user_or_not(self.uid, self.uname)


class ThreadEmailingToAllSubs(Thread):
    def __init__(self, uid, text):
        """Инициализация потока"""
        Thread.__init__(self)
        self.text = text
        self.uid = uid

    def run(self):
        us.emailing_to_all_subs_keyboard(self.uid, self.text)


class ThreadSendDataToUON(Thread):
    def __init__(self, data, uid):
        """Инициализация потока"""
        Thread.__init__(self)
        self.data = data
        self.uid = uid

    def run(self):
        us.send_data_to_uon(self.data, self.uid)


class ThreadSendMsgMuch(Thread):
    def __init__(self, user_ids, text):
        """Инициализация потока"""
        Thread.__init__(self)
        self.user_ids = user_ids
        self.text = text

    def run(self):
        vk.send_message_much(self.user_ids, self.text)


def send_message(uid, msg, keyboard=None):
    t = ThreadSendMsg(uid, msg, keyboard)
    t.start()


def new_user_or_not(uid, uname):
    t = ThreadNewUserOrNote(uid, uname)
    t.start()


def send_msg_welcome(uid, uname, keyboard, group_id=cfg.group_id):
    t = ThreadSendMsgWelcome(uid, uname, keyboard, group_id)
    t.start()


def emailing_to_all_subs_keyboard(uid, text):
    t = ThreadEmailingToAllSubs(uid, text)
    t.start()


def send_data_to_uon(data, uid):
    t = ThreadSendDataToUON(data, uid)
    t.start()


def send_msg_much(user_ids, text):
    t = ThreadSendMsgMuch(user_ids, text)
    t.start()
