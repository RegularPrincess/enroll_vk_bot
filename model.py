#!/usr/bin/python
# -*- coding: utf-8 -*-

import consts as cnst
import datetime as dt

class Admin:
    def __init__(self, uid, name, status='member'):
        self.uid = uid
        self.name = name
        # self.status = status


class Follower:
    def __init__(self, uid, name, status='member', written_on_course=0, mess_allowed=0):
        self.uid = uid
        self.name = name
        self.status = status
        self.written_on_course = written_on_course
        self.mess_allowed = mess_allowed

    def is_msging_allowed(self):
        return self.mess_allowed == 1 and not self.status == cnst.USER_LEAVE_STATUS


class EnrollInfo:
    def __init__(self, uid):
        self.uid = uid
        self.name = None
        self.email = None
        self.number = None
        self.where = None
        self.who = None
        self.when = None
        self.budget = None
        self.quests = None
        self.answers = []

    def name_is_sign(self):
        return self.name is not None

    def email_is_sign(self):
        return self.email is not None

    def number_is_sign(self):
        return self.number is not None

    def set_name(self, name):
        self.name = name

    def set_email(self, email):
        if self.name_is_sign():
            self.email = email
        else:
            raise BaseException()

    def set_number(self, number):
        if self.name_is_sign() and self.email_is_sign():
            self.number = number
        else:
            raise BaseException()

    def reset(self):
        self.name = None
        self.email = None
        self.number = None


# broadcast by time
class BcstByTime:
    def __init__(self, start_date=None, time=None, repet_days=None, msg=None, id=None):
        self.start_date = start_date
        self.time = time
        self.repet_days = repet_days
        self.msg = msg
        self.id = id

    def date_time_is_not_sign(self):
        return self.start_date is None or self.time is None or self.repet_days is None

#
# class QuestMsgs:
#     def __init__(self):
#         self.quests = []
#

class QuestMsg:
    def __init__(self, id=None, quest=None, answs=None):
        self.id = id
        self.quest = quest
        self.answs = answs
