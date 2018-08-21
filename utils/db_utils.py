#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlite3 import dbapi2 as sqlite3

import config
import consts as cnst
import model as m
from utils import vklib
import datetime


with sqlite3.connect(config.db_name) as connection:
    cursor = connection.cursor()
    sql = '''CREATE TABLE IF NOT EXISTS known_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        uid INTEGER UNIQUE NOT NULL,
        status TEXT NOT NULL,
        name TEXT NOT NULL,
        written_on_course INTEGER DEFAULT 0,
        mess_allowed INTEGER DEFAULT 0)'''
    cursor.execute(sql)
    sql = '''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        uid INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL)'''
    cursor.execute(sql)
    sql = '''CREATE TABLE IF NOT EXISTS bcst_by_time (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            start_date TEXT NOT NULL,
            time TEXT NOT NULL,
            repet_days INTEGER NOT NULL,
            msg TEXT NOT NULL )'''
    cursor.execute(sql)
    sql = '''CREATE TABLE IF NOT EXISTS leave_reason (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                reason TEXT NOT NULL )'''
    cursor.execute(sql)
    # cursor.execute("DROP TABLE IF EXISTS quest_msg")
    sql = '''CREATE TABLE IF NOT EXISTS quest_msg (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    quest TEXT NOT NULL,
                    answs TEXT NOT NULL)'''
    cursor.execute(sql)
    sql = '''CREATE INDEX IF NOT EXISTS uid_known_users ON known_users (uid)'''
    cursor.execute(sql)
    # Add base admins to bot
    sql = '''INSERT OR IGNORE INTO admins (uid, name) VALUES ({!s}, '{!s}')'''.format(
        config.admin_id, config.admin_name)
    cursor.execute(sql)
    connection.commit()


def vk_emailing_to_all_subs(text):
    """
    Разослать текст всем подписчикам, кому возможно группы
    """
    count = 0
    arr = []
    users = get_bot_followers()
    for u in users:
        if u.is_msging_allowed():
            arr.append(u.uid)
            count += 1
        if len(arr) == 100:
            vklib.send_message_much(arr, text)
            arr = []
    vklib.send_message_much(arr, text)
    return count


def get_bot_admins():
    """
    Получить админов бота
    """
    arr = []
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM admins'''
        res = cursor.execute(sql).fetchall()
        print(res)
        for x in res:
            arr.append(m.Admin(x[1], x[2]))
        connection.commit()
    return arr


def get_list_bot_admins():
    """
    Получить админов бота как список
    """
    arr = []
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM admins'''
        res = cursor.execute(sql).fetchall()
        print(res)
        for x in res:
            arr.append(x[1])
        connection.commit()
    return arr


def is_admin(uid):
    admins = get_list_bot_admins()
    return uid in admins


def delete_admin(admin_id):
    """
    Удалить админа
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''DELETE FROM admins WHERE uid=?'''
        cursor.execute(sql, (admin_id,))
        connection.commit()


def add_bot_admin(uid, name):
    """
    Добавить админа бота
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''INSERT OR IGNORE INTO admins (uid, name) VALUES (?, ?)'''
        cursor.execute(sql, (uid, name))
        connection.commit()


def set_bot_follower_status(uid, status):
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''UPDATE known_users SET status=? WHERE uid=?'''
        cursor.execute(sql, (status, uid))
        connection.commit()


def set_bot_follower_mess_allowed(uid, status):
    """
    status = 0(not allow) or 1(allow)
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''UPDATE known_users SET mess_allowed=? WHERE uid=?'''
        cursor.execute(sql, (status, uid))
        connection.commit()


def add_bot_follower(uid, name, status=cnst.USER_SUB_STATUS, msg_allowed=0):
    """
    Добавить подписчика бота
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        if follower_is_leave(uid):
            set_bot_follower_status(uid, cnst.USER_RETURN_STATUS)
        else:
            sql = '''INSERT OR IGNORE INTO known_users (uid, status, name, mess_allowed) VALUES (?, ?, ?, ?)'''
            cursor.execute(sql, (uid, status, name, msg_allowed))
        connection.commit()


def get_bot_followers(only_id=False):
    """
    Получить подписчиков бота
    """
    arr = []
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM known_users'''
        res = cursor.execute(sql).fetchall()
        print(res)
        for x in res:
            item = x[1] if only_id else m.Follower(x[1], x[3], x[2], x[4], x[5])
            arr.append(item)
        connection.commit()
    return arr


def follower_is_leave(uid):
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT count(*) FROM known_users ku WHERE uid == ? AND status = ?'''
        cursor.execute(sql, (uid, cnst.USER_LEAVE_STATUS))
        res = cursor.fetchone()
        count = int(res[0])
        connection.commit()
        return count != 0


def get_msg_allowed_count():
    """
    Количество разрешивших себе писать
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT count(*) FROM known_users ku WHERE mess_allowed == 1 AND NOT status = ?'''
        cursor.execute(sql, (cnst.USER_LEAVE_STATUS, ))
        res = cursor.fetchone()
        count = int(res[0])
        connection.commit()
        return count


def is_known_user(uid):
    """
    Есть ли пользователь в базе
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM known_users WHERE uid = ? '''
        res = cursor.execute(sql, (uid, )).fetchall()
        return len(res) > 0


def get_bcsts_by_time():
    """
    Получить все рассылки бота
    """
    arr = []
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM bcst_by_time'''
        res = cursor.execute(sql).fetchall()
        print(res)
        for x in res:
            item = m.BcstByTime(id=x[0], repet_days=x[3], msg=x[4])
            item.start_date = datetime.datetime.strptime(x[1], '%Y-%m-%d').date()
            item.time = datetime.datetime.strptime(x[2], '%H:%M').time()
            arr.append(item)
        connection.commit()
    return arr


def add_bcst(bcst):
    """
    Добавить рассылку
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''INSERT OR IGNORE INTO bcst_by_time (start_date, time, repet_days, msg) VALUES (?, ?, ?, ?)'''
        cursor.execute(sql, (bcst.start_date.strftime("%Y-%m-%d"), bcst.time.strftime("%H:%M"), bcst.repet_days, bcst.msg))
        connection.commit()


def delete_bcst(id):
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''DELETE FROM bcst_by_time WHERE id=?'''
        cursor.execute(sql, (id,))
        connection.commit()


def add_leave_reason(reason):
    """
    Добавить причину отписки
    """
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''INSERT OR IGNORE INTO leave_reason (reason) VALUES (?)'''
        cursor.execute(sql, (reason,))
        connection.commit()


def delete_all_leave_reason():
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''DELETE FROM leave_reason'''
        cursor.execute(sql)
        connection.commit()


def get_leave_reasons():
    """
    Получить причины отпички
    """
    arr = []
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM leave_reason'''
        res = cursor.execute(sql).fetchall()
        print(res)
        for x in res:
            item = x[1]
            arr.append(item)
        connection.commit()
    return arr


def add_quest_msg(quest, answs, id=None):
    if id is not None:
        update_quest(quest, answs, id)
    else:
        with sqlite3.connect(config.db_name) as connection:
            cursor = connection.cursor()
            sql = '''INSERT OR IGNORE INTO quest_msg (quest, answs) VALUES (?, ?)'''
            cursor.execute(sql, (quest, answs))
            connection.commit()


def delete_quest_msg(id):
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''DELETE FROM quest_msg WHERE id=?'''
        cursor.execute(sql, (id,))
        connection.commit()


def get_quest_msgs():
    arr = []
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''SELECT * FROM quest_msg'''
        res = cursor.execute(sql).fetchall()
        print(res)
        for x in res:
            item = m.QuestMsg(x[0], x[1], x[2])
            arr.append(item)
        connection.commit()
    return arr


def update_quest(quest, answs, id):
    with sqlite3.connect(config.db_name) as connection:
        cursor = connection.cursor()
        sql = '''UPDATE quest_msg SET quest=?, answs=? WHERE id=?'''
        cursor.execute(sql, (quest, answs, id))
        connection.commit()
