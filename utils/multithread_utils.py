import os
import config as cfg
from threading import Thread
import utils.service_utils as utils
import consts as cnst

import time

from datetime import datetime, date, timedelta

import utils.db_utils as db
import utils.vklib as vk
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
            db.vk_emailing_to_all_subs(self.bcst.msg)
            time.sleep(61)


class ThreadParseGroup(Thread):
    def __init__(self, uid, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.group_id = group_id

    def run(self):
        members_count = utils.get_group_count()
        msg = cnst.MSG_MEMBERS_COUNT.format(members_count)
        vk.send_message(self.uid, msg)
        vk.send_message(self.uid, cnst.MSG_PLEASE_STAND_BY)
        added_count = utils.parse_group(members_count)
        msg = cnst.MSG_ADDED_COUNT.format(added_count)
        vk.send_message(self.uid, msg)


class ThreadSubs(Thread):
    def __init__(self, uid, group_id=cfg.group_id):
        """Инициализация потока"""
        Thread.__init__(self)
        self.uid = uid
        self.group_id = group_id

    def run(self):
        vk.send_message(self.uid, cnst.MSG_PLEASE_STAND_BY)
        vk_doc_link = utils.make_subs_file(self.uid)
        vk.send_message_doc(self.uid, cnst.MSG_SUBS, vk_doc_link)