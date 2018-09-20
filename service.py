#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utils.vklib as vk
import config as cfg
import consts as cnst
import model as m
from utils import service_utils as utils
import utils.multithread_utils as mt
from utils import db_utils as db

READY_TO_ENROLL = {}
IN_ADMIN_PANEL = {}
READY_TO_LEAVE = {}
thread_manager = mt.ThreadManager()
TIMEOUT_THREADS = {}

thread_manager.run_brdcst_shedule()
utils.send_message_admins_after_restart()


def admin_message_processing(uid, uname, text):
    if text == cnst.MSG_ADMIN_EXIT:
        utils.del_uid_from_dict(uid, IN_ADMIN_PANEL)
        mt.send_msg_welcome(uid, uname, utils.get_user_keyboard())

    elif text == cnst.BTN_BROADCAST:
        IN_ADMIN_PANEL[uid] = cnst.BTN_BROADCAST
        all_count = vk.get_count_group_followers(cfg.group_id)
        msg_allowed_count = db.get_msg_allowed_count()
        mt.send_message(uid, cnst.MSG_USER_SHORT_INFO.format(all_count, msg_allowed_count))
        mt.send_message(uid, cnst.MSG_ACCEPT_BROADCAST, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_SUBS:
        pg = mt.ThreadSubs(uid)
        pg.start()

    elif text == cnst.BTN_ADMINS:
        IN_ADMIN_PANEL[uid] = cnst.BTN_ADMINS
        admins = db.get_bot_admins()
        msg = cnst.MSG_ADMINS
        for a in admins:
            msg += '🔑 {}, id - {}\n\n'.format(a.name, a.uid)
        msg += cnst.MSG_ADMIN_REMOVING
        mt.send_message(uid, msg, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_ADD_ADMIN:
        IN_ADMIN_PANEL[uid] = cnst.BTN_ADD_ADMIN
        mt.send_message(uid, cnst.MSG_ADMIN_ADDING, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_ADD_BROADCAST_BY_TIME:
        IN_ADMIN_PANEL[uid] = m.BcstByTime()
        mt.send_message(uid, cnst.MSG_ADD_BRDCST_BY_TIME, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_BROADCAST_BY_TIME:
        IN_ADMIN_PANEL[uid] = cnst.BTN_BROADCAST_BY_TIME
        brtcst = db.get_bcsts_by_time()
        msg = '🔥 Запланированные рассылки 🔥\n\n'
        for a in brtcst:
            msg += cnst.MSG_PLANNED_BCST.format(a.start_date, a.time, a.repet_days, a.id, a.msg)
        msg += 'Для удаления рассылки введите её id.'
        mt.send_message(uid, msg, cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_QUESTIONS:
        IN_ADMIN_PANEL[uid] = m.QuestMsg()
        msg = utils.get_quest_msgs_as_str()
        mt.send_message(uid, msg)
        mt.send_message(uid, cnst.MSG_ACCEPT_QUEST_MSG, cnst.KEYBOARD_CANCEL_AND_MSG_EDIT)

    elif text == cnst.BTN_FIRST_MSG_EDIT:
        IN_ADMIN_PANEL[uid] = cnst.BTN_FIRST_MSG_EDIT
        msg = db.get_first_msg()
        msg += "\n\n Отправьте новое приветственное сообщение для замены. Используйте {} для обращения к пользователю."
        mt.send_message(uid, msg, keyboard=cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_MAIL_MSG_EDIT:
        IN_ADMIN_PANEL[uid] = cnst.BTN_MAIL_MSG_EDIT
        msg = db.get_mail_quest()
        msg += "\n\n Отправьте новое сообщение запроса email для замены."
        mt.send_message(uid, msg, keyboard=cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_NUMBER_MSG_EDIT:
        IN_ADMIN_PANEL[uid] = cnst.BTN_NUMBER_MSG_EDIT
        msg = db.get_number_quest()
        msg += "\n\n Отправьте новое сообщение запроса номера для замены."
        mt.send_message(uid, msg, keyboard=cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_FIRST_BTN_EDIT:
        IN_ADMIN_PANEL[uid] = cnst.BTN_FIRST_BTN_EDIT
        msg = db.get_first_btn()
        msg += "\n\n Отправьте новый текст кнопки для замены."
        mt.send_message(uid, msg, keyboard=cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_LAST_MSG_EDIT:
        IN_ADMIN_PANEL[uid] = cnst.BTN_LAST_MSG_EDIT
        msg = db.get_last_msg()
        msg += "\n\n Отправьте новый текст последнего сообщения для замены. ({} - обращение к пользователю)"
        mt.send_message(uid, msg, keyboard=cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_COLOR_BTN_EDIT:
        IN_ADMIN_PANEL[uid] = cnst.BTN_COLOR_BTN_EDIT
        msg = db.get_color_btn()
        msg += "\n\n Выберите новый цвет из предложеных"
        k = utils.get_keyboard_from_list(cnst.BTN_COLORS_MAP.keys(), cnst.cancel_btn)
        mt.send_message(uid, msg, k)

    elif text.lower() == cnst.CMD_PARSE_GROUP:
        if db.is_admin(uid):
            pg = mt.ThreadParseGroup(uid)
            pg.start()
        else:
            mt.send_message(uid, cnst.MSG_YOU_NOT_ADMIN, utils.get_user_keyboard())

    elif text == cnst.BTN_LEAVE_REASON:
        IN_ADMIN_PANEL[uid] = cnst.BTN_LEAVE_REASON
        reasons = utils.get_leave_reasons_as_str()
        if reasons == '':
            reasons = '<Не указано ни одной>'
        mt.send_message(uid, cnst.MSG_LEAVE_REASON.format(reasons), cnst.KEYBOARD_CANCEL)

    elif text == cnst.BTN_CANCEL:
        IN_ADMIN_PANEL[uid] = ''
        mt.send_message(uid, cnst.MSG_CANCELED_MESSAGE, cnst.KEYBOARD_ADMIN)

    elif isinstance(IN_ADMIN_PANEL[uid], m.BcstByTime):
        if IN_ADMIN_PANEL[uid].date_time_is_not_sign():
            bcst = utils.parse_bcst(text)
            IN_ADMIN_PANEL[uid] = bcst
            if bcst is None:
                mt.send_message(uid, "Некорректный формат. (22.08.2018 15:22 3)")
            else:
                mt.send_message(uid, cnst.MSG_ACCEPT_BROADCAST)
        else:
            IN_ADMIN_PANEL[uid].msg = text
            mt.send_message(uid, 'Рассылка создана!', cnst.KEYBOARD_ADMIN)
            thread_manager.add_brcst_thread(IN_ADMIN_PANEL[uid])
            IN_ADMIN_PANEL[uid] = None

    elif isinstance(IN_ADMIN_PANEL[uid], m.QuestMsg):
        try:
            if IN_ADMIN_PANEL[uid].quest is not None:
                int('not int')
            qid = int(text)
            utils.del_question(qid)
            mt.send_message(uid, "Удалено", cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            qid_str = text.split(' ')[0]

            if utils.isint(qid_str) and \
                            IN_ADMIN_PANEL[uid].quest is None and IN_ADMIN_PANEL[uid].id is None:
                IN_ADMIN_PANEL[uid].id = int(qid_str)
                text = ' '.join(text.split(' ')[1:])
            if IN_ADMIN_PANEL[uid].quest is None:
                IN_ADMIN_PANEL[uid].quest = text
                mt.send_message(uid, cnst.MSG_ADDING_ANSWS_VAR, cnst.KEYBOARD_END_AND_CANCELE)
            elif text == cnst.BTN_END:
                utils.add_quest_msg(IN_ADMIN_PANEL[uid].quest, '', IN_ADMIN_PANEL[uid].id)
                mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
                IN_ADMIN_PANEL[uid] = ''
            else:
                utils.add_quest_msg(IN_ADMIN_PANEL[uid].quest, text, IN_ADMIN_PANEL[uid].id)
                mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
                IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_BROADCAST:
        mt.emailing_to_all_subs_keyboard(uid, text)
        IN_ADMIN_PANEL.clear()
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_FIRST_MSG_EDIT:
        db.update_first_msg(text)
        mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_MAIL_MSG_EDIT:
        db.update_mail_quest(text)
        mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_NUMBER_MSG_EDIT:
        db.update_number_quest(text)
        mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_FIRST_BTN_EDIT:
        db.update_first_btn(text)
        mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_LAST_MSG_EDIT:
        db.update_last_msg(text)
        mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_COLOR_BTN_EDIT:
        color = cnst.BTN_COLORS_MAP[text]
        if color is None:
            mt.send_message(uid, "Выберите из предложенных")
        else:
            db.update_color_btn(color)
            mt.send_message(uid, "Сохранено", cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_ADMINS:
        try:
            admin_id = int(text)
            db.delete_admin(admin_id)
            msg = cnst.MSG_ADMIN_REMOVED
            mt.send_message(uid, msg, cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            msg = cnst.MSG_VALUE_ERROR
            mt.send_message(uid, msg)

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_ADD_ADMIN:
        try:
            admin_id = int(text)
            name = vk.get_user_name(admin_id)
            db.add_bot_admin(admin_id, name)
            mt.send_message(uid, cnst.MSG_ADMIN_SUCCCES_ADDED, cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            msg = cnst.MSG_VALUE_ERROR
            mt.send_message(uid, msg)

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_BROADCAST_BY_TIME:
        try:
            id = int(text)
            thread_manager.delete_brcst(id)
            mt.send_message(uid, "Запланированная рассылка удалена", cnst.KEYBOARD_ADMIN)
            IN_ADMIN_PANEL[uid] = ''
        except ValueError:
            msg = cnst.MSG_VALUE_ERROR
            mt.send_message(uid, msg)

    elif IN_ADMIN_PANEL[uid] == cnst.BTN_LEAVE_REASON:
        db.delete_all_leave_reason()
        count = utils.save_leave_reasons(text)
        mt.send_message(uid, cnst.MSG_LEAVE_REASON_SAVED.format(str(count)), cnst.KEYBOARD_ADMIN)
        IN_ADMIN_PANEL[uid] = ''
    else:
        pass
        # mt.send_message(uid, cnst.MSG_DEFAULT_ANSWER)


def message_processing(uid, text):
    uname = db.get_follower_name(uid)
    if uname is None:
        mt.new_user_or_not(uid, uname, send_welcome=True)
    if uid in IN_ADMIN_PANEL:
        admin_message_processing(uid, uname, text)
        return 'ok'

    if text.lower() in cnst.START_WORDS and not_ready_to_enroll(uid):
        thread = mt.ThreadSendMsgWelcome(uid, uname, utils.get_user_keyboard())
        thread.start()
        thread = mt.ThreadNewUserOrNote(uid, uname)
        thread.start()

    elif db.get_first_btn().lower() in text.lower() or (text.lower() in cnst.USER_ACCEPT_WORDS and not_ready_to_enroll(uid)):
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
            mt.send_message(uid, q.quest.format(READY_TO_ENROLL[uid].name), k)
        else:
            msg = db.get_mail_quest()
            mt.send_message(uid, msg.format(READY_TO_ENROLL[uid].name), cnst.KEYBOARD_END_AND_SKIP)
            READY_TO_ENROLL[uid].quests.pop(0)

    elif text == cnst.BTN_CANCEL:
        if uid in READY_TO_ENROLL:
            # READY_TO_ENROLL[uid].answers.clear()
            READY_TO_ENROLL[uid].answers.append('Пользователь не завершил процедуру.')
            # READY_TO_ENROLL[uid].number = ''
            # READY_TO_ENROLL[uid].email = ''
            mt.send_msg_to_admins(READY_TO_ENROLL[uid])
            mt.send_data_to_uon(READY_TO_ENROLL[uid], uid)
        if uid in TIMEOUT_THREADS:
            TIMEOUT_THREADS[uid].stop()
            utils.del_uid_from_dict(uid, TIMEOUT_THREADS)
        utils.del_uid_from_dict(uid, READY_TO_ENROLL)
        mt.send_message(uid, cnst.MSG_CANCELED_MESSAGE, utils.get_user_keyboard())

    # Обработка ввода данных пользователя
    elif uid in READY_TO_ENROLL:
        if len(READY_TO_ENROLL[uid].quests) > 0:
            if len(READY_TO_ENROLL[uid].quests) == 1:
                READY_TO_ENROLL[uid].answers.append(text)
                msg = db.get_mail_quest()
                mt.send_message(uid, msg.format(READY_TO_ENROLL[uid].name), cnst.KEYBOARD_END_AND_SKIP)
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
                mt.send_message(uid, q.quest.format(READY_TO_ENROLL[uid].name), k)
        elif not READY_TO_ENROLL[uid].email_is_sign():
            READY_TO_ENROLL[uid].set_name(uname)
            if utils.is_email_valid(text):
                READY_TO_ENROLL[uid].set_email(text)
                msg = db.get_number_quest()
                mt.send_message(uid, msg, cnst.KEYBOARD_CANCEL)
            else:
                if text == cnst.BTN_SKIP:
                    READY_TO_ENROLL[uid].set_email('')
                    msg = db.get_number_quest()
                    mt.send_message(uid, msg.format(READY_TO_ENROLL[uid].name), cnst.KEYBOARD_CANCEL)
                else:
                    mt.send_message(uid, cnst.MSG_UNCORECT_EMAIL)
        elif not READY_TO_ENROLL[uid].number_is_sign():
            if utils.is_number_valid(text):
                READY_TO_ENROLL[uid].set_number(text)
                msg = db.get_last_msg()
                mt.send_message(uid, msg.format(READY_TO_ENROLL[uid].name),
                                utils.get_user_keyboard())
                mt.send_msg_to_admins(READY_TO_ENROLL[uid])
                mt.send_data_to_uon(READY_TO_ENROLL[uid], uid)
                READY_TO_ENROLL[uid] = None
                utils.del_uid_from_dict(uid, READY_TO_ENROLL)
                TIMEOUT_THREADS[uid].stop()
                utils.del_uid_from_dict(uid, TIMEOUT_THREADS)
            else:
                mt.send_message(uid, cnst.MSG_UNCORECT_NUMBER)
        if uid in TIMEOUT_THREADS and uid in READY_TO_ENROLL:
            TIMEOUT_THREADS[uid].update()
        elif uid in READY_TO_ENROLL:
            TIMEOUT_THREADS[uid] = mt.ThreadSendDataByTimeout(READY_TO_ENROLL[uid], uid)

    elif uid in READY_TO_LEAVE:
        mt.send_message(uid, cnst.MSG_THANK_YOU, utils.get_user_keyboard())
        mt.send_message(uid, cnst.GROUP_LEAVE_MESSAGE.format(uname))
        admins = db.get_list_bot_admins()
        mt.send_msg_much(admins, cnst.MSG_USER_LEAVED.format(uname, uid, text))
        utils.del_uid_from_dict(uid, READY_TO_LEAVE)

    # Вход для админа
    elif text.lower() in cnst.ADMIN_KEY_WORDS and not_ready_to_enroll(uid):
        if db.is_admin(uid):
            IN_ADMIN_PANEL[uid] = ''
            mt.send_message(uid, cnst.MSG_ADMIN_PANEL, cnst.KEYBOARD_ADMIN)
        else:
            mt.send_message(uid, cnst.MSG_YOU_NOT_ADMIN, utils.get_user_keyboard())
    elif text.lower() == "clearme":
        mt.send_message(uid, "clear", keyboard=cnst.EMPTY_KEYBOARD)
    else:
        mt.new_user_or_not(uid, uname, send_welcome=True)
        # mt.send_msg_welcome(uid, uname, cnst.KEYBOARD_USER)
        # mt.send_message(uid, cnst.MSG_DEFAULT_ANSWER)
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
    mt.send_message(uid, cnst.MSG_LEAVING, k)
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
    msg = db.get_first_msg()
    mt.send_message(uid, msg.format(uname), utils.get_user_keyboard())
    utils.del_uid_from_dict(uid, IN_ADMIN_PANEL)
    utils.del_uid_from_dict(uid, READY_TO_ENROLL)
    utils.del_uid_from_dict(uid, READY_TO_LEAVE)
    return 'ok'


def message_allow(uid):
    db.set_bot_follower_mess_allowed(uid, 1)
    uname = vk.get_user_name(uid)
    mt.new_user_or_not(uid, uname)
    mt.send_msg_welcome(uid, uname, utils.get_user_keyboard())
    return 'ok'


def message_deny(uid):
    db.set_bot_follower_mess_allowed(uid, 0)
    return 'ok'

