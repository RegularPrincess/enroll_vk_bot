import datetime
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import SQLAlchemyError
import consts as cnst
import config
import model as m

PER_PAGE = 20

Base = automap_base()
engine = create_engine("postgresql://postgres:postgres@localhost:5432/heroku")
session = Session(engine)
# reflect the tables
Base.prepare(engine, reflect=True)


def is_not_table(table_name):
    return table_name not in name_tables


def get_table_page(table_name, page):
    try:
        query = session.query(eval(table_name)).slice(page * PER_PAGE, (page * PER_PAGE) + PER_PAGE)
        return query
    except SQLAlchemyError as err:
        session.rollback()
        return err


def get_filtered_rows(table_name, col, val):
    try:
        query = session.query(eval(table_name)).filter(eval(table_name + '.' + col) == val)
        return query
    except SQLAlchemyError as err:
        session.rollback()
        return err


def delete_table_row(table_name, dict_obj):
    row_obj = eval(table_name + '()')
    for field, val in dict_obj.items():
        setattr(row_obj, field, val)

    filter_param = {}
    for key in inspect(eval(table_name)).primary_key:
        filter_param[key.name] = row_obj.__dict__[key.name]
    query = session.query(eval(table_name)). \
        filter_by(**filter_param)
    obj_from_table = query.first()
    try:
        session.delete(obj_from_table)
        session.commit()
        return 'Ok'
    except SQLAlchemyError as err:
        session.rollback()
        return err


def update_table_row(table_name, dict_obj):
    filter_param = {}
    for key in inspect(eval(table_name)).primary_key:
        filter_param[key.name] = dict_obj[key.name]

    query = session.query(eval(table_name)). \
        filter_by(**filter_param)
    obj_from_table = query.first()

    for field, val in dict_obj.items():
        setattr(obj_from_table, field, val)
    try:
        session.merge(obj_from_table)
        session.commit()
        return 'Ok'
    except SQLAlchemyError as err:
        session.rollback()
        return err


sql = '''CREATE TABLE IF NOT EXISTS known_users (
        id SERIAL PRIMARY KEY,
        uid INTEGER UNIQUE NOT NULL,
        status TEXT NOT NULL,
        name TEXT NOT NULL,
        written_on_course INTEGER DEFAULT 0,
        mess_allowed INTEGER DEFAULT 0)'''
result = engine.execute(sql)
print(result)

sql = '''CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        uid INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL)'''
result = engine.execute(sql)
print(result)

sql = '''CREATE TABLE IF NOT EXISTS bcst_by_time (
            id SERIAL PRIMARY KEY,
            start_date TEXT NOT NULL,
            time TEXT NOT NULL,
            repet_days INTEGER NOT NULL,
            msg TEXT NOT NULL )'''
result = engine.execute(sql)
print(result)

sql = '''CREATE TABLE IF NOT EXISTS leave_reason (
                id SERIAL PRIMARY KEY,
                reason TEXT NOT NULL )'''
result = engine.execute(sql)
print(result)

sql = '''CREATE TABLE IF NOT EXISTS quest_msg (
                    id SERIAL PRIMARY KEY,
                    quest TEXT NOT NULL,
                    answs TEXT NOT NULL)'''
result = engine.execute(sql)
print(result)

# cursor.execute('DROP TABLE IF EXISTS msgs')
sql = '''CREATE TABLE IF NOT EXISTS msgs (
           id SERIAL PRIMARY KEY,
           first_msg TEXT NOT NULL UNIQUE,
           mail_request TEXT NOT NULL,
           number_request TEXT NOT NULL,
           first_btn TEXT NOT NULL,
           color_btn TEXT NOT NULL,
           last_msg TEXT,
           uniq INTEGER DEFAULT 0 UNIQUE)'''
result = engine.execute(sql)
print(result)
sql = '''CREATE INDEX IF NOT EXISTS uid_known_users ON known_users (uid)'''
result = engine.execute(sql)
print(result)

# Add base admins to bot
sql = '''INSERT INTO admins (uid, name) VALUES ({!s}, '{!s}') ON CONFLICT DO NOTHING'''.format(
    config.admin_id, config.admin_name)
result = engine.execute(sql)
print(result)

sql = '''INSERT INTO admins (uid, name)  VALUES (259056624, 'Yuriy')  ON CONFLICT DO NOTHING'''
result = engine.execute(sql)
print(result)

sql = '''INSERT INTO msgs (first_msg, mail_request, number_request, first_btn, color_btn, last_msg) 
            VALUES ('{}', '{}', '{}', '{}', '{}', '{}')  ON CONFLICT DO NOTHING'''.format(cnst.MSG_WELCOME_FOLLOWER,
                                                                                          cnst.MSG_ACCEPT_EMAIL,
                                                                                          cnst.MSG_ACCEPT_NUMBER,
                                                                                          cnst.BTN_ENROLL, "positive",
                                                                                          cnst.LAST_MSG)
result = engine.execute(sql)
print(result)

known_users = Base.classes.known_users
admins = Base.classes.admins
leave_reason = Base.classes.leave_reason
quest_msg = Base.classes.quest_msg
bcst_by_time = Base.classes.bcst_by_time
msgs = Base.classes.msgs
name_tables = ['known_users', 'admins', 'bcst_by_time', 'leave_reason', 'quest_msg', 'msgs']


def get_bot_admins():
    """
    Получить админов бота
    """
    arr = []
    sql = '''SELECT * FROM admins'''
    res = engine.execute(sql)
    print(res)
    for x in res:
        arr.append(m.Admin(x[1], x[2]))
        return arr


def get_list_bot_admins():
    """
    Получить админов бота как список
    """
    arr = []

    sql = '''SELECT * FROM admins'''
    res = engine.execute(sql)
    print(res)
    for x in res:
        arr.append(x[1])
        return arr


def is_admin(uid):
    admins = get_list_bot_admins()
    return uid in admins


def delete_admin(admin_id):
    """
    Удалить админа
    """
    sql = '''DELETE FROM admins WHERE uid= %s'''
    engine.execute(sql, admin_id)


def add_bot_admin(uid, name):
    """
    Добавить админа бота
    """
    sql = '''INSERT INTO admins (uid, name) VALUES (%s, %s) ON CONFLICT DO NOTHING'''
    engine.execute(sql, uid, name)


def set_bot_follower_status(uid, status):
    sql = '''UPDATE known_users SET status = %s WHERE uid = %s'''
    engine.execute(sql, status, uid)


def set_bot_follower_mess_allowed(uid, status):
    """
    status = 0(not allow) or 1(allow)
    """
    sql = '''UPDATE known_users SET mess_allowed=%s WHERE uid=%s'''
    engine.execute(sql, status, uid)
    

def follower_is_leave(uid):
    sql = '''SELECT count(*) FROM known_users ku WHERE uid = %s AND status = %s'''
    res = engine.execute(sql, uid, cnst.USER_LEAVE_STATUS)
    res = res.fetchone()
    count = int(res[0])
    return count != 0


def add_bot_follower(uid, name, status=cnst.USER_SUB_STATUS, msg_allowed=0):
    """
    Добавить подписчика бота
    """
    if follower_is_leave(uid):
        set_bot_follower_status(uid, cnst.USER_RETURN_STATUS)
    else:
        sql = '''INSERT INTO known_users (uid, status, name, mess_allowed) 
          VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING'''
        engine.execute(sql, uid, status, name, msg_allowed)


def get_bot_followers(only_id=False):
    """
    Получить подписчиков бота
    """
    arr = []

    sql = '''SELECT * FROM known_users'''
    res = engine.execute(sql)
    print(res)
    for x in res:
        item = x[1] if only_id else m.Follower(x[1], x[3], x[2], x[4], x[5])
        arr.append(item)
    return arr


def get_follower_name(uid):
    sql = '''SELECT name FROM known_users ku WHERE uid = %s'''
    res = engine.execute(sql, uid)
    res = res.fetchone()
    if res is None:
        name = None
    else:
        name = res[0]
    return name


def get_msg_allowed_count():
    """
    Количество разрешивших себе писать
    """
    sql = '''SELECT count(*) FROM known_users ku WHERE mess_allowed = 1 AND NOT status = %s'''
    res = engine.execute(sql, cnst.USER_LEAVE_STATUS)
    res = res.fetchone()
    count = int(res[0])
    return count


def is_known_user(uid):
    """
    Есть ли пользователь в базе
    """
    sql = '''SELECT * FROM known_users WHERE uid = %s '''
    res = engine.execute(sql, uid).fetchall()
    return len(res) > 0


def get_bcsts_by_time():
    """
    Получить все рассылки бота
    """
    arr = []
    sql = '''SELECT * FROM bcst_by_time'''
    res = engine.execute(sql)
    print(res)
    for x in res:
        item = m.BcstByTime(id=x[0], repet_days=x[3], msg=x[4])
        item.start_date = datetime.datetime.strptime(x[1], '%Y-%m-%d').date()
        item.time = datetime.datetime.strptime(x[2], '%H:%M').time()
        arr.append(item)
    return arr


def add_bcst(bcst):
    """
    Добавить рассылку
    """
    sql = '''INSERT INTO bcst_by_time (start_date, time, repet_days, msg) 
      VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING'''
    engine.execute(sql, bcst.start_date.strftime("%Y-%m-%d"), bcst.time.strftime("%H:%M"), bcst.repet_days, bcst.msg)


def delete_bcst(id):
    sql = '''DELETE FROM bcst_by_time WHERE id=%s'''
    engine.execute(sql, id)


def add_leave_reason(reason):
    """
    Добавить причину отписки
    """
    sql = '''INSERT OR IGNORE INTO leave_reason (reason) VALUES (%s)'''
    engine.execute(sql, reason)


def delete_all_leave_reason():
    sql = '''DELETE FROM leave_reason'''
    engine.execute(sql)


def get_leave_reasons():
    """
    Получить причины отпички
    """
    arr = []
    sql = '''SELECT * FROM leave_reason'''
    res = engine.execute(sql)
    print(res)
    for x in res:
        item = x[1]
        arr.append(item)
    return arr


def update_quest(quest, answs, id):
    sql = '''UPDATE quest_msg SET quest=%s, answs=%s WHERE id=%s'''
    engine.execute(sql, quest, answs, id)


def add_quest_msg(quest, answs, id=None):
    if id is not None:
        update_quest(quest, answs, id)
    else:
        sql = '''INSERT INTO quest_msg (quest, answs) VALUES (%s, %s) ON CONFLICT DO NOTHING'''
        engine.execute(sql, quest, answs)


def delete_quest_msg(id):
    sql = '''DELETE FROM quest_msg WHERE id=%s'''
    engine.execute(sql, id)


def get_quest_msgs():
    arr = []
    sql = '''SELECT * FROM quest_msg'''
    res = engine.execute(sql)
    print(res)
    for x in res:
        item = m.QuestMsg(x[0], x[1], x[2])
        arr.append(item)
    return arr


def get_first_msg():
    sql = '''SELECT first_msg FROM msgs'''
    res = engine.execute(sql).fetchone()
    print(res)
    return res[0]


def update_first_msg(first_msg):
    sql = '''UPDATE msgs SET first_msg=%s'''
    res = engine.execute(sql, first_msg)
    print(res)


def get_mail_quest():
    sql = '''SELECT mail_request FROM msgs'''
    res = engine.execute(sql).fetchone()
    print(res[0])
    return res[0]


def update_mail_quest(mail_quest):
    sql = '''UPDATE msgs SET mail_request=%s'''
    res = engine.execute(sql, mail_quest)
    print(res)


def get_number_quest():
    sql = '''SELECT number_request FROM msgs'''
    res = engine.execute(sql).fetchone()
    print(res)
    return res[0]


def update_number_quest(number_quest):
    sql = '''UPDATE msgs SET number_request=%s'''
    res = engine.execute(sql, number_quest)
    print(res)


def get_first_btn():
    sql = '''SELECT first_btn FROM msgs'''
    res = engine.execute(sql).fetchone()
    print(res)
    return res[0]


def update_first_btn(first_btn):
    sql = '''UPDATE msgs SET first_btn=%s'''
    res = engine.execute(sql, first_btn)
    print(res)


def get_color_btn():
    sql = '''SELECT color_btn FROM msgs'''
    res = engine.execute(sql).fetchone()
    print(res)
    return res[0]


def update_color_btn(color_btn):
    sql = '''UPDATE msgs SET color_btn=%s'''
    res = engine.execute(sql, color_btn)
    print(res)


def get_last_msg():
    sql = '''SELECT last_msg FROM msgs'''
    res = engine.execute(sql).fetchone()
    print(res)
    return res[0]


def update_last_msg(last_msg):
    sql = '''UPDATE msgs SET last_msg=%s'''
    res = engine.execute(sql, last_msg)
    print(res)
update_last_msg("gsdhjkfhghj")
