#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utils.vklib as vk

import config as cfg
import consts as cnst
import model as m
from utils import db_utils as db
from utils import service_utils as utils
import utils.multithread_utils as mt

READY_TO_ENROLL = {}
IN_ADMIN_PANEL = {}
READY_TO_LEAVE = {}
thread_manager = mt.ThreadManager()

thread_manager.run_brdcst_shedule()
utils.send_message_admins_after_restart()


def admin_message_processing(uid, uname, text):
    if text == cnst.MSG_ADMIN_EXIT:
        utils.del_uid_from_dict(uid, IN_ADMIN_PANEL)
        vk.send_message_keyboard(uid, cnst.MSG_WELCOME_TO_COURSE.format(uname), cnst.KEYBOARD_USER)

    elif text == cnst.BTN_BROADCAST:
        IN_ADMIN_PANEL[uid] = cnst.BTN_BROADCAST
        all_count = vk.get_count_group_followers(cfg.group_id)
        msg_allowed_count = db.get_msg_allowed_count()
        vk.send_message(uid, cnst.MSG_USER_SHORT_INFO.format(all_count, msg_allowed_count))
        vk.send_message_keyboard(uid, cnst.MSG_ACCEPT_BROADCAST, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_SUBS:
        vk.send_message(uid, cnst.MSG_PLEASE_STAND_BY)
        vk_doc_link = utils.make_subs_file(uid)
        vk.send_message_doc(uid, cnst.MSG_SUBS, vk_doc_link)

    elif text == cnst.BTN_ADMINS:
        IN_ADMIN_PANEL[uid] = cnst.BTN_ADMINS
        admins = db.get_bot_admins()
        msg = cnst.MSG_ADMINS
        for a in admins:
            msg += '🔑 {}, id - {}\n\n'.format(a.name, a.uid)
        msg += cnst.MSG_ADMIN_REMOVING
        vk.send_message_keyboard(uid, msg, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_ADD_ADMIN:
        IN_ADMIN_PANEL[uid] = cnst.BTN_ADD_ADMIN
        vk.send_message_keyboard(uid, cnst.MSG_ADMIN_ADDING, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_ADD_BROADCAST_BY_TIME:
        IN_ADMIN_PANEL[uid] = m.BcstByTime()
        vk.send_message_keyboard(uid, cnst.MSG_ADD_BRDCST_BY_TIME, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_BROADCAST_BY_TIME:
        IN_ADMIN_PANEL[uid] = cnst.BTN_BROADCAST_BY_TIME
        brtcst = db.get_bcsts_by_time()
        msg = '🔥 Запланированные рассылки 🔥\n\n'
        for a in brtcst:
            msg += cnst.MSG_PLANNED_BCST.format(a.start_date, a.time, a.repet_days, a.id, a.msg)
        msg += 'Для удаления рассылки введите её id.'
        vk.send_message_keyboard(uid, msg, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_QUESTIONS:
        IN_ADMIN_PANEL[uid] = m.QuestMsg()
        msg = utils.get_quest_msgs_as_str()
        vk.send_message(uid, msg)
        vk.send_message_keyboard(uid, cnst.MSG_ACCEPT_QUEST_MSG, cnst.KEYBOARD_CANCEL)

    elif text.lower() == cnst.CMD_PARSE_GROUP:
        if db.is_admin(uid):
            members_count = utils.get_group_count()
            msg = cnst.MSG_MEMBERS_COUNT.format(members_count)
            vk.send_message(uid, msg)
            vk.send_message(uid, cnst.MSG_PLEASE_STAND_BY)
            added_count = utils.parse_group(members_count)
            msg = cnst.MSG_ADDED_COUNT.format(added_count)
            vk.send_message(uid, msg)
        else:
            vk.send_message_keyboard(uid, cnst.MSG_YOU_NOT_ADMIN, cnst.KEYBOARD_USER)

    elif text == cnst.BTN_LEAVE_REASON:
        IN_ADMIN_PANEL[uid] = cnst.BTN_LEAVE_REASON
        reasons = utils.get_leave_reasons_as_str()
        if reasons == '':
            reasons = '<Не указано ни одной>'
        vk.send_message_keyboard(uid, cnst.MSG_LEAVE_REASON.format(reasons), cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_CANCEL:
        IN_ADMIN_PANEL[uid] = ''
        vk.send_message_keyboard(uid, cnst.MSG_CANCELED_MESSAGE, cnst.KEYBOARD_ADMIN)

    elif isinstance(IN_ADMIN_PANEL[uid], m.BcstByTime):
        if IN_ADMIN_PANEL[uid].date_time_is_not_sign():
            bcst = utils.parse_bcst(text)
            IN_ADMIN_PANEL[uid] = bcst
            if bcst is None:
                vk.send_message(uid, "Некорректный формат. (22.08.2018 15:22 3)")
            else:
                vk.send_message(uid, cnst.MSG_ACCEPT_BROADCAST)
        else:
            IN_ADMIN_PANEL[uid].msg = text
            vk.send_message_keyboard(uid, 'Рассылка создана!', cnst.KEYBOARD_ADMIN)
            thread_manager.add_brcst_thread(IN_ADMIN_PANEL[uid])
            IN_ADMIN_PANEL[uid] = None

    elif isinstance(IN_ADMIN_PANEL[uid], m.QuestMsg):
        try:
            if IN_ADMIN_PANEL[uid].quest is not None:
                int('not int')
            qid = int(text)
            utils.del_question(qid)
            vk.send_message_keyboard(uid, "Удалено", cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            qid_str = text.split(' ')[0]

            if utils.isint(qid_str) and \
                            IN_ADMIN_PANEL[uid].quest is None and IN_ADMIN_PANEL[uid].id is None:
                IN_ADMIN_PANEL[uid].id = int(qid_str)
                text = ' '.join(text.split(' ')[1:])
            if IN_ADMIN_PANEL[uid].quest is None:
                IN_ADMIN_PANEL[uid].quest = text
                vk.send_message_keyboard(uid, cnst.MSG_ADDING_ANSWS_VAR, cnst.KEYBOARD_END_AND_CANCELE)
            elif text == cnst.BTN_END:
                utils.add_quest_msg(IN_ADMIN_PANEL[uid].quest, '', IN_ADMIN_PANEL[uid].id)
                vk.send_message_keyboard(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
                IN_ADMIN_PANEL[uid] = ''
            else:
                utils.add_quest_msg(IN_ADMIN_PANEL[uid].quest, text, IN_ADMIN_PANEL[uid].id)
                vk.send_message_keyboard(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
                IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_BROADCAST:
        count = db.vk_emailing_to_all_subs(text)
        vk.send_message_keyboard(uid, cnst.MSG_BROADCAST_COMPLETED.format(count), cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_ADMINS:
        try:
            admin_id = int(text)
            db.delete_admin(admin_id)
            msg = cnst.MSG_ADMIN_REMOVED
            vk.send_message_keyboard(uid, msg, cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            msg = cnst.MSG_VALUE_ERROR
            vk.send_message(uid, msg)

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_ADD_ADMIN:
        try:
            admin_id = int(text)
            name = vk.get_user_name(admin_id)
            db.add_bot_admin(admin_id, name)
            vk.send_message_keyboard(uid, cnst.MSG_ADMIN_SUCCCES_ADDED, cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            msg = cnst.MSG_VALUE_ERROR
            vk.send_message(uid, msg)

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_BROADCAST_BY_TIME:
        try:
            id = int(text)
            thread_manager.delete_brcst(id)
            vk.send_message_keyboard(uid, "Запланированная рассылка удалена", cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            msg = cnst.MSG_VALUE_ERROR
            vk.send_message(uid, msg)

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_LEAVE_REASON:
        db.delete_all_leave_reason()
        count = utils.save_leave_reasons(text)
        vk.send_message_keyboard(uid, cnst.MSG_LEAVE_REASON_SAVED.format(str(count)), cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''
    else:
        pass
        # vk.send_message(uid, cnst.MSG_DEFAULT_ANSWER)


def message_processing(uid, text):
    uname = vk.get_user_name(uid)
    if uid in IN_ADMIN_PANEL:
        admin_message_processing(uid, uname, text)
        return 'ok'

    if text.lower() in cnst.START_WORDS:
        vk.send_message_keyboard(uid, cnst.MSG_WELCOME_TO_COURSE.format(uname), cnst.KEYBOARD_USER)
        utils.new_user_or_not(uid, uname)

    elif text == cnst.BTN_ENROLL or (text.lower() in cnst.USER_ACCEPT_WORDS and not_ready_to_enroll(uid)):
        READY_TO_ENROLL[uid] = m.EnrollInfo(uid)
        quests = db.get_quest_msgs()
        quests.append('FAKE')
        READY_TO_ENROLL[uid].quests = quests
        READY_TO_ENROLL[uid].set_name(uname)
        k = None
        if len(READY_TO_ENROLL[uid].quests) > 1:
            q = READY_TO_ENROLL[uid].quests.pop(0)
            if len(q.answs) > 0:
                answrs = q.answs.split('; ')
                k = utils.get_keyboard_from_list(answrs, cnst.cancel_btn)
            else:
                k = cnst.KEYBOARD_CANCEL
            vk.send_message_keyboard(uid, q.quest, k)
        else:
            vk.send_message_keyboard(uid, cnst.MSG_ACCEPT_EMAIL, cnst.KEYBOARD_END_AND_SKIP)
            READY_TO_ENROLL[uid].quests.pop(0)

    elif text == cnst.BTN_CANCEL:
        if uid in READY_TO_ENROLL:
            READY_TO_ENROLL[uid].answers.clear()
            READY_TO_ENROLL[uid].answers.append('Пользователь не завершил процедуру.')
            READY_TO_ENROLL[uid].number = ''
            READY_TO_ENROLL[uid].email = ''
            utils.send_data_to_uon(READY_TO_ENROLL[uid], uid)
        utils.del_uid_from_dict(uid, READY_TO_ENROLL)
        vk.send_message_keyboard(uid, cnst.MSG_CANCELED_MESSAGE, cnst.KEYBOARD_USER)

    # Обработка ввода данных пользователя
    elif uid in READY_TO_ENROLL:
        if len(READY_TO_ENROLL[uid].quests) > 0:
            if len(READY_TO_ENROLL[uid].quests) == 1:
                READY_TO_ENROLL[uid].answers.append(text)
                vk.send_message_keyboard(uid, cnst.MSG_ACCEPT_EMAIL, cnst.KEYBOARD_END_AND_SKIP)
                READY_TO_ENROLL[uid].quests.pop(0)
            else:
                k = None
                READY_TO_ENROLL[uid].answers.append(text)
                q = READY_TO_ENROLL[uid].quests.pop(0)
                if len(q.answs) > 0:
                    answrs = q.answs.split('; ')
                    k = utils.get_keyboard_from_list(answrs, cnst.cancel_btn)
                else:
                    k = cnst.KEYBOARD_CANCEL
                vk.send_message_keyboard(uid, q.quest, k)
        elif not READY_TO_ENROLL[uid].email_is_sign():
            if utils.is_email_valid(text):
                READY_TO_ENROLL[uid].set_email(text)
                vk.send_message_keyboard(uid, cnst.MSG_ACCEPT_NUMBER, cnst.KEYBOARD_CANCEL)
            else:
                if text == cnst.BTN_SKIP:
                    READY_TO_ENROLL[uid].set_email('')
                    vk.send_message_keyboard(uid, cnst.MSG_ACCEPT_NUMBER, cnst.KEYBOARD_CANCEL)
                else:
                    vk.send_message(uid, cnst.MSG_UNCORECT_EMAIL)
        elif not READY_TO_ENROLL[uid].number_is_sign():
            if utils.is_number_valid(text):
                READY_TO_ENROLL[uid].set_number(text)
                vk.send_message_keyboard(uid, cnst.MSG_ENROLL_COMPLETED.format(READY_TO_ENROLL[uid].name),
                                         cnst.KEYBOARD_USER)
                utils.send_message_admins(READY_TO_ENROLL[uid])
                utils.send_data_to_uon(READY_TO_ENROLL[uid], uid)
                READY_TO_ENROLL[uid] = None
                utils.del_uid_from_dict(uid, READY_TO_ENROLL)
            else:
                vk.send_message(uid, cnst.MSG_UNCORECT_NUMBER)

    elif uid in READY_TO_LEAVE:
        vk.send_message_keyboard(uid, cnst.MSG_THANK_YOU, cnst.KEYBOARD_USER)
        vk.send_message(uid, cnst.GROUP_LEAVE_MESSAGE.format(uname))
        admins = db.get_list_bot_admins()
        vk.send_message_much(admins, cnst.MSG_USER_LEAVED.format(uname, uid, text))
        utils.del_uid_from_dict(uid, READY_TO_LEAVE)

    # Вход для админа
    elif text.lower() in cnst.ADMIN_KEY_WORDS and not_ready_to_enroll(uid):
        if db.is_admin(uid):
            IN_ADMIN_PANEL[uid] = ''
            vk.send_message_keyboard(uid, cnst.MSG_ADMIN_PANEL, cnst.KEYBOARD_ADMIN)
        else:
            vk.send_message_keyboard(uid, cnst.MSG_YOU_NOT_ADMIN, cnst.KEYBOARD_USER)
    else:
        utils.new_user_or_not(uid, uname)
        # vk.send_message(uid, cnst.MSG_DEFAULT_ANSWER)
    return 'ok'


def not_ready_to_enroll(uid):
    return uid not in READY_TO_ENROLL


def group_leave(uid):
    db.set_bot_follower_status(uid, cnst.USER_LEAVE_STATUS)
    utils.del_uid_from_dict(uid, IN_ADMIN_PANEL)
    utils.del_uid_from_dict(uid, READY_TO_ENROLL)
    READY_TO_LEAVE[uid] = None
    reasons = db.get_leave_reasons()
    k = utils.get_keyboard_from_list(reasons)
    vk.send_message_keyboard(uid, cnst.MSG_LEAVING, k)
    return 'ok'


def group_join(uid):
    uname = vk.get_user_name(uid)
    if uname == '':
        uname = 'No Name'
    msg_allowed = 0
    if vk.is_messages_allowed(uid):
        msg_allowed = 1
    if db.is_known_user(uid):
        db.set_bot_follower_status(uid, cnst.USER_SUB_STATUS)
    else:
        db.add_bot_follower(uid, uname,  msg_allowed=msg_allowed)
    vk.send_message_keyboard(uid, cnst.MSG_WELCOME_TO_COURSE.format(uname), cnst.KEYBOARD_USER)
    utils.del_uid_from_dict(uid, IN_ADMIN_PANEL)
    utils.del_uid_from_dict(uid, READY_TO_ENROLL)
    utils.del_uid_from_dict(uid, READY_TO_LEAVE)
    return 'ok'


def message_allow(uid):
    db.set_bot_follower_mess_allowed(uid, 1)
    uname = vk.get_user_name(uid)
    utils.new_user_or_not(uid, uname)
    return 'ok'


def message_deny(uid):
    db.set_bot_follower_mess_allowed(uid, 0)
    return 'ok'
