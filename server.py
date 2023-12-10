#!/usr/bin/env python


# This is a simple web server for a training record application.
# It's your job to extend it by adding the backend functionality to support
# recording training in an SQL database. You will also need to support
# user access/session control. You should only need to extend this file.
# The client side code (html, javascript and css) is complete and does not
# require editing or detailed understanding, it serves only as a
# debugging/development aid.

# import the various libraries needed
import http.cookies as Cookie  # some cookie handling support
from http.server import BaseHTTPRequestHandler, HTTPServer  # the heavy lifting of the web server
import urllib  # some url parsing support
import json  # support for json encoding
import sys  # needed for agument handling
import sqlite3  # sql database
import random  # generate random numbers
import time  # needed to record when stuff happened
import datetime


def random_digits(n):
    """This function provides a random integer with the specfied number of digits and no leading zeros."""
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return random.randint(range_start, range_end)


# The following three functions issue SQL queries to the database.

def do_database_execute(op, get_primary_key=False):
    """Execute an sqlite3 SQL query to database.db that does not expect a response."""
    print(op)
    try:
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute(op)
        db.commit()
        generated_key = cursor.lastrowid
        print("created")
        return generated_key if get_primary_key else None
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


def do_database_fetchone(op):
    """Execute an sqlite3 SQL query to database.db that expects to extract a single row result. Note, it may be a null result."""
    print(op)
    try:
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute(op)
        result = cursor.fetchone()
        print(result)
        db.close()
        return result
    except Exception as e:
        print(e)
        return None


def do_database_fetchall(op):
    """Execute an sqlite3 SQL query to database.db that expects to extract a multi-row result. Note, it may be a null result."""
    print(op)
    try:
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute(op)
        result = cursor.fetchall()
        print(result)
        db.close()
        return result
    except Exception as e:
        print(e)
        return None


# The following build_ functions return the responses that the front end client understands.
# You can return a list of these.

def build_response_message(code, text):
    """This function builds a message response that displays a message
       to the user on the web page. It also returns an error code."""
    return {"type": "message", "code": code, "text": text}


def build_response_skill(id, name, gained, trainer, state):
    """This function builds a summary response that contains one summary table entry."""
    return {"type": "skill", "id": id, "name": name, "gained": gained, "trainer": trainer, "state": state}


def build_response_class(id, name, trainer, when, notes, size, max, action):
    """This function builds an activity response that contains the id and name of an activity type,"""
    return {"type": "class", "id": id, "name": name, "trainer": trainer, "when": when, "notes": notes, "size": size,
            "max": max, "action": action}


def build_response_attendee(id, name, action):
    """This function builds an activity response that contains the id and name of an activity type,"""
    return {"type": "attendee", "id": id, "name": name, "action": action}


def build_response_redirect(where):
    """This function builds the page redirection response
       It indicates which page the client should fetch.
       If this action is used, it should be the only response provided."""
    return {"type": "redirect", "where": where}


def check_if_session_valid(imagic, iuser):
    # Todo: check this function working
    magic_current = do_database_fetchone(f'SELECT magic FROM session WHERE userid = {iuser}')
    if not magic_current:
        return True
    return magic_current[0] == imagic


def get_userid(username):
    userid = do_database_fetchone(f'SELECT userid FROM users WHERE username = "{username}"')
    return userid


def check_password_for_username(username, password):
    res = do_database_fetchone(f'SELECT password FROM users WHERE username = "{username}"')[0]
    return res == password


# The following handle_..._request functions are invoked by the corresponding /action?command=.. request
def handle_login_request(iuser, imagic, content):
    """A user has supplied a username and password. Check if these are
       valid and if so, create a suitable session record in the database
       with a random magic identifier that is returned.
       Return the username, magic identifier and the response action set."""
    username = content['username']
    password = content['password']
    response = []
    if not username:
        response.append(build_response_message(100, 'Please provide a username.'))
        return [iuser, imagic, response]
    if not password:
        response.append(build_response_message(101, 'Please provide a password.'))
        return [iuser, imagic, response]
    userid = get_userid(username)
    if not userid:
        response.append(build_response_message(200, 'Username: ' + username + ' does not exist.'))
        return [iuser, imagic, response]
    iuser = userid[0]
    if not check_password_for_username(username, password):
        response.append(build_response_message(201, 'Incorrect password.'))
        return [iuser, imagic, response]
    imagic = random_digits(10)
    do_database_execute(f'DELETE FROM session WHERE userid = "{iuser}"')
    do_database_execute(f'INSERT INTO session (userid, magic) VALUES ({iuser},{imagic})')
    response.append({"type": "redirect", "where": "\index.html"})
    return [iuser, imagic, response]


def handle_logout_request(iuser, imagic, parameters):
    """This code handles the selection of the logout button.
       You will     print(content)
    need to ensure the end of the session is recorded in the database
        And that the session magic is revoked."""
    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]
    do_database_execute(f'Delete From session Where userid = {iuser}')
    response.append({"type": "redirect", "where": "\logout.html"})
    return [iuser, imagic, response]


def format_my_returns(tuple_in):
    out = []
    for val in tuple_in:
        out.append(val[0])
    return tuple(out)


def get_states_of_users(statuses):
    states = []
    for status in statuses:
        match (status):
            case 0:
                states.append("enrolled")
            case 1:
                states.append("passed")
            case 2:
                states.append("failed")
            case 3:
                states.append("cancelled")
            case 4:
                states.append("removed")
            case other:
                states.append(None)
    return states


def get_trainer_names(trainer_ids):
    if isinstance(trainer_ids, int):
        name = do_database_fetchone(f'SELECT fullname FROM users WHERE userid = {trainer_ids}')
        if name:
            return name[0]
        return None
    trainer_names = []
    for id in trainer_ids:
        name = do_database_fetchone(f'SELECT fullname FROM users WHERE userid = {id}')
        if name:
            trainer_names.append(name[0])
    return trainer_names


def get_skill_names(skill_ids):
    if isinstance(skill_ids, int):
        skill = do_database_fetchone(f'SELECT name FROM skill WHERE skillid = {skill_ids}')
        if skill:
            return skill[0]
        return None
    skills = []
    for val in skill_ids:
        skill = do_database_fetchone(f'SELECT name FROM skill WHERE skillid = {val}')
        if skill:
            skills.append(skill[0])
    return skills


def get_skillids_start_trainerids(class_ids):
    skill_ids = []
    trainer_ids = []
    start_dates = []
    if isinstance(class_ids, int):
        out = do_database_fetchone(f'SELECT skillid, start, trainerid FROM class WHERE classid = {class_ids}')
        if out:
            skill_ids = out[0]
            start_dates = out[1]
            trainer_ids = out[2]
        return skill_ids, start_dates, trainer_ids
    for id in class_ids:
        out = do_database_fetchone(f'SELECT skillid, trainerid, start FROM class WHERE classid = {id}')
        if out:
            skill_ids.append(out[0])
            trainer_ids.append(out[1])
            start_dates.append(out[2])
    return skill_ids, start_dates, trainer_ids


def handle_get_my_skills_request(iuser, imagic):
    """This code handles a request for a list of a users skills.
       You must return a value for all vehicle types, even when it's zero."""

    response = []
    print(iuser, imagic)
    check_session = check_if_session_valid(imagic, iuser)
    print(check_session)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    class_ids = format_my_returns(do_database_fetchall(f'SELECT classid FROM attendee WHERE userid = {iuser}'))
    statuses = format_my_returns(do_database_fetchall(f'SELECT status FROM attendee WHERE userid = {iuser}'))
    skill_ids, start_dates, trainer_ids = get_skillids_start_trainerids(class_ids)
    skill_names = get_skill_names(skill_ids)
    trainer_names = get_trainer_names(trainer_ids)
    states = get_states_of_users(statuses)

    indices_to_skip = []
    user_is_trainer = do_database_fetchall(f'SELECT trainerid, skillid FROM trainer WHERE trainerid = {iuser}')
    for i in range(len(class_ids)):
        if states[i] in ["cancelled", "removed"]:
            indices_to_skip.append(i)
        elif states[i] == 'enrolled':
            if int(start_dates[i]) >= int(time.time()):
                states[i] = "scheduled"
            elif int(start_dates[i]) < int(time.time()):
                states[i] = "pending"
        for row_trainer in user_is_trainer:
            s_id = row_trainer[1]
            if s_id == skill_ids[i]:
                states[i] = "trainer"

    for i in range(len(class_ids)):
        if i in indices_to_skip:
            continue
        response.append(build_response_skill(skill_ids[i], skill_names[i], start_dates[i], trainer_names[i], states[i]))

    # Todo:
    #  You have to arrange the responses according to the state and date as shown in the pdf
    #  Also check all the checks here
    response.append(build_response_message(0, 'Skills list provided.'))
    return [iuser, imagic, response]


def get_class_size_max_size_notes(class_ids):
    if isinstance(class_ids, int):
        note = do_database_fetchone(f'SELECT note FROM class WHERE classid = {class_ids}')[0]
        c_size = len(do_database_fetchall(f'SELECT userid FROM attendee WHERE classid = {class_ids}'))
        m_size = do_database_fetchone(f'SELECT max FROM class WHERE classid = {class_ids}')[0]
        return c_size, m_size, note
    notes = []
    class_sizes = []
    max_sizes = []
    for id in class_ids:
        note = do_database_fetchone(f'SELECT note FROM class WHERE classid = {id}')[0]
        notes.append(note)
        c_size = len(do_database_fetchall(f'SELECT userid FROM attendee WHERE classid = {id}'))
        class_sizes.append(c_size)
        m_size = do_database_fetchone(f'SELECT max FROM class WHERE classid = {id}')[0]
        max_sizes.append(m_size)
    return class_sizes, max_sizes, notes


def get_actions(class_ids, class_sizes, iuser, max_sizes, skill_ids):
    actions = ['join' for _ in range(len(class_ids))]
    for i, id in enumerate(class_ids):
        user_status = do_database_fetchall(f'Select status From attendee Where userid = {iuser} And classid = {id}')
        print('user statuses = ', user_status)
        if user_status:
            for status in user_status:
                if status[0] == 0:
                    actions[i] = 'leave'
                if status[0] == 4:
                    actions[i] = 'unavailable'
        user_has_skill = do_database_fetchone(
            f'SELECT attendee.* FROM attendee JOIN class ON attendee.classid = class.classid WHERE attendee.userid = {iuser} AND (attendee.status = 1 OR attendee.status = 0) AND class.skillid = {skill_ids[i]} AND attendee.classid != {id}')
        if user_has_skill:
            actions[i] = 'unavailable'
        is_user_trainer_for_skill = do_database_fetchone(
            f'Select * From trainer Where trainerid = {iuser} and skillid = {skill_ids[i]}')
        if is_user_trainer_for_skill:
            actions[i] = 'unavailable'
        is_user_trainer = do_database_fetchone(f'Select * From class Where classid = {id} And trainerid = {iuser}')
        if is_user_trainer:
            actions[i] = 'edit'
        if class_sizes[i] == max_sizes[i]:
            actions[i] = 'unavailable'
        if max_sizes[i] == 0:
            actions[i] = 'cancelled'
    return actions


def handle_get_upcoming_request(iuser, imagic):
    """This code handles a request for the details of a class.
       """
    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    class_ids = format_my_returns(do_database_fetchall(f'SELECT classid FROM class'))
    skill_ids, start, trainer_ids = get_skillids_start_trainerids(class_ids)
    skill_names = get_skill_names(skill_ids)
    trainer_names = get_trainer_names(trainer_ids)
    class_sizes, max_sizes, notes = get_class_size_max_size_notes(class_ids)
    actions = get_actions(class_ids, class_sizes, iuser, max_sizes, skill_ids)

    for i in range(len(class_ids)):
        if int(start[i]) <= int(time.time()):
            continue
        response.append(
            build_response_class(class_ids[i], skill_names[i], trainer_names[i], notes[i], start[i], class_sizes[i],
                                 max_sizes[i], actions[i]))

    response.append(build_response_message(0, 'Upcoming class list provided.'))
    return [iuser, imagic, response]


def handle_get_class_detail_request(iuser, imagic, content):
    """This code handles a request for a list of upcoming classes.
       """
    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    class_id = content['id']
    skill_id, start_date, trainer_id = get_skillids_start_trainerids(class_id)
    if str(iuser) != str(trainer_id):
        print("iuser: ", iuser)
        print('trainer_id: ', trainer_id)
        response.append(build_response_message(210, 'Cannot show class: User has to be a trainer'))
        return [iuser, imagic, response]

    skill_name = get_skill_names(skill_id)

    attendee_id_user_ids_statuses = do_database_fetchall(
        f'Select attendeeid, userid, status From attendee Where classid = {class_id}')
    attendeee_ids = []
    user_ids = []
    statuses = []
    for row in attendee_id_user_ids_statuses:
        attendeee_ids.append(row[0])
        user_ids.append(row[1])
        statuses.append(row[2])
    names = []
    for id in user_ids:
        name = do_database_fetchone(f'Select fullname From users Where userid = {id}')
        names.append(name)

    states = []
    for status in statuses:
        if status == 0:
            if int(start_date) >= int(time.time()):
                states.append('remove')
            else:
                states.append('update')
        elif status == 1:
            states.append('passed')
        elif status == 2:
            states.append('failed')
        elif status == 3:
            states.append('cancelled')

    trainer_name = get_trainer_names(trainer_id)
    class_size, max_size, note = get_class_size_max_size_notes(class_id)

    if max_size == 0:
        action = 'cancelled'
    else:
        action = 'cancel'

    response.append(
        build_response_class(class_id, skill_name, trainer_name, note, start_date, class_size,
                             max_size, action))

    for i in range(len(attendeee_ids)):
        response.append(build_response_attendee(attendeee_ids[i], names[i], states[i]))

    # Todo:
    #  - check all checks in here
    #  - refactor
    return [iuser, imagic, response]


def handle_join_class_request(iuser, imagic, content):
    """This code handles a request by a user to join a class.
      """
    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]
    class_id = content['id']
    skill_id, start_date, trainer_id = get_skillids_start_trainerids(class_id)
    skill_name = get_skill_names(skill_id)
    trainer_name = get_trainer_names(trainer_id)
    class_size, max_size, note = get_class_size_max_size_notes(class_id)
    if class_size == max_size:
        response.append(build_response_message(220, 'Cannot join class: Class is full'))
        return [iuser, imagic, response]
    if trainer_id == iuser:
        response.append(build_response_message(221, 'Cannot join class: User is trainer so cannot join class.'))
        return [iuser, imagic, response]
    user_already_in_class = do_database_fetchone(
        f'Select * From attendee Where userid = {iuser} and classid = {class_id} and status = 0')
    if user_already_in_class:
        response.append(build_response_message(222, 'Cannot join class: User already enrolled in class.'))
        return [iuser, imagic, response]
    user_already_passed_class = do_database_fetchone(
        f'Select * From attendee Where userid = {iuser} and classid = {class_id} and status = 1')
    if user_already_passed_class:
        response.append(build_response_message(223, 'Cannot join class: User already passed class.'))
    user_has_skill = do_database_fetchone(
        f'SELECT attendee.* FROM attendee JOIN class ON attendee.classid = class.classid WHERE attendee.userid = {iuser} AND (attendee.status = 1 OR attendee.status = 0) AND class.skillid = {skill_id} AND attendee.classid != {class_id}')
    if user_has_skill:
        response.append(build_response_message(224, 'Cannot join class: User already has this skill or enrolled in a '
                                                    'class for this skill'))
        return [iuser, imagic, response]
    if max_size == 0:
        response.append(build_response_message(225, 'Cannot join class: This class has been cancelled by the trainer'))
        return [iuser, imagic, response]
    user_has_been_removed = do_database_fetchone(
        f'Select * From attendee Where userid = {iuser} and classid = {class_id} and status = 4')
    if user_has_been_removed:
        response.append(build_response_message(226, 'Cannot join class: User has been removed from this class, '
                                                    'so cannot rejoin'))
        return [iuser, imagic, response]
    is_user_trainer_for_skill = do_database_fetchone(f'Select * From trainer Where trainerid = {iuser}')
    if is_user_trainer_for_skill:
        response.append(build_response_message(227, 'Cannot join class: User is listed as a trainer for this skill'))

    user_has_left = do_database_fetchone(
        f'Select * From attendee WHERE classid = {class_id} and userid = {iuser} and status = 3')
    if user_has_left:
        do_database_execute(f'UPDATE attendee SET status = 0 WHERE userid = {iuser} AND classid = {class_id}')
    else:
        do_database_execute(f'Insert Into attendee (userid, classid, status) Values ({iuser}, {class_id}, 0)')

    response.append(
        build_response_class(class_id, skill_name, trainer_name, start_date, note, class_size + 1, max_size, 'leave')
    )
    response.append(
        build_response_message(0, "Successfully joined class.")
    )

    return [iuser, imagic, response]


def handle_leave_class_request(iuser, imagic, content):
    """This code handles a request by a user to leave a class.
    """
    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]
    class_id = content['id']
    skill_id, start_date, trainer_id = get_skillids_start_trainerids(class_id)
    skill_name = get_skill_names(skill_id)
    trainer_name = get_trainer_names(trainer_id)
    class_size, max_size, note = get_class_size_max_size_notes(class_id)
    user_enrolled = do_database_fetchone(f'Select * From attendee Where userid = {iuser} and classid = {class_id}')
    if not user_enrolled:
        response.append(build_response_message(230, 'Cannot leave class: User not enrolled in class'))
        return [iuser, imagic, response]
    user_cancelled = do_database_fetchone(
        f'Select * From attendee Where userid = {iuser} and status = 3 and classid = {class_id}')
    if user_cancelled:
        response.append(build_response_message(231, 'Cannot leave class: User already left class'))
        return [iuser, imagic, response]
    user_removed = do_database_fetchone(
        f'Select * From attendee Where userid = {iuser} and status = 4 and classid = {class_id}')
    if user_removed:
        response.append(build_response_message(232, 'Cannot leave class: User has been removed from class'))
        return [iuser, imagic, response]
    if trainer_id == iuser:
        response.append(build_response_message(233, "Cannot leave class: user is the trainer of this class"))
        return [iuser, imagic, response]
    if int(start_date) <= int(time.time()):
        response.append(build_response_message(231, 'Cannot leave class: Class has already started'))
        return [iuser, imagic, response]

    do_database_execute(f'UPDATE attendee SET status = 3 WHERE userid = {iuser} AND classid = {class_id}')
    response.append(
        build_response_class(class_id, skill_name, trainer_name, start_date, note, class_size, max_size, 'join'))
    response.append(build_response_message(0, 'Successfully left class'))
    return [iuser, imagic, response]


def handle_cancel_class_request(iuser, imagic, content):
    """This code handles a request to cancel an entire class."""

    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    class_id = content['id']
    skill_id, start_date, trainer_id = get_skillids_start_trainerids(class_id)
    if str(iuser) != str(trainer_id):
        response.append(build_response_message(240,
                                               'Cannot cancel class: User has to be the registered trainer in order to cancel a class'))
        return [iuser, imagic, response]

    do_database_execute(f'Update class Set max = 0 Where classid = {class_id}')
    class_size, max_size, note = get_class_size_max_size_notes(class_id)
    skill_name = get_skill_names(skill_id)
    trainer_name = get_trainer_names(trainer_id)
    max_size = 0
    response.append(
        build_response_class(class_id, skill_name, trainer_name, note, start_date, class_size, max_size, 'cancelled'))

    attendee_ids = do_database_fetchall(f'Select attendeeid From attendee Where classid = {class_id}')
    if attendee_ids:
        for user in attendee_ids:
            is_enrolled = do_database_fetchone(f'Select * From attendee Where attendeeid = {user[0]} and status = 0')
            if is_enrolled:
                do_database_execute(f'Update attendee Set status = 3 Where attendeeid = {user[0]}')
        user_ids = do_database_fetchall(f'Select userid From attendee Where classid = {class_id}')
        names = []
        for id in user_ids:
            name = do_database_fetchone(f'Select fullname From users Where userid = {id[0]}')
            names.append(name)

        for i in range(len(attendee_ids)):
            response.append(build_response_attendee(attendee_ids[i], names[i], "cancelled"))

    response.append(build_response_message(0, 'Cancelled class successfully'))

    return [iuser, imagic, response]


def handle_update_attendee_request(iuser, imagic, content):
    """This code handles a request to cancel a user attendance at a class by a trainer"""

    response = []
    check_session = check_if_session_valid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    attendee_id = content['id']
    state_input = content['state']
    attendee_user_id = do_database_fetchone(f'Select userid From attendee Where attendeeid = {attendee_id}')
    if not attendee_user_id:
        response.append(
            build_response_message(250, 'Cannot update attendee: Attendee deos not exist, deleted entry successfully.'))
        do_database_execute(f'Delete from attendee Where attendeeid = {attendee_id}')
        return [iuser, imagic, response]
    name = do_database_fetchone(f'Select fullname From users Where userid = {attendee_user_id[0]}')
    if not name:
        response.append(
            build_response_message(250, 'Cannot update attendee: Attendee deos not exist, deleted entry successfully.'))
        do_database_execute(f'Delete from attendee Where attendeeid = {attendee_id}')
        return [iuser, imagic, response]

    if state_input == "pass":
        new_state = 'passed'
        status_table = 1
    elif state_input == 'fail':
        new_state = 'failed'
        status_table = 2
    elif state_input == 'remove':
        new_state = 'removed'
        status_table = 4
    else:
        response.append(
            build_response_message(251, 'Cannot update attendee: Please input a valid new state (pass/fail/remove)'))
        return [iuser, imagic, response]

    do_database_execute(f'Update attendee Set status = {status_table} Where attendeeid = {attendee_id}')
    response.append(build_response_attendee(attendee_id, name[0], new_state))

    return [iuser, imagic, response]


def handle_create_class_request(iuser, imagic, content):
    """This code handles a request to create a class."""

    response = []
    skill_id = content['id']
    day = content['day']
    month = content['month']
    year = content['year']
    hour = content['hour']
    minute = content['minute']
    note = content['note']
    max_students = content['max']

    is_trainer_for_skill = do_database_fetchone(f'Select * From trainer Where trainerid = {iuser}')
    if not is_trainer_for_skill:
        response.append(
            build_response_message(260, 'Cannot create class: User is not a listed trainer for this skill.'))

    skill_name = get_skill_names(skill_id)

    if not skill_name:
        response.append(build_response_message(261, 'Cannot create class: Skill not listed in database.'))
        return [iuser, imagic, response]

    trainer_name = get_trainer_names(iuser)

    try:
        start_date = int(datetime.datetime(year, month, day, hour, minute).timestamp())
        print("Datetime created:", start_date)
    except ValueError as e:
        response.append(build_response_message(262, 'Cannot create class: Invalid Date or Time.'))
        return [iuser, imagic, response]

    if start_date < int(time.time()):
        response.append(build_response_message(263, 'Cannot create class: start time must be in the future.'))
        return [iuser, imagic, response]

    if max_students > 10 or max_students < 1:
        response.append(
            build_response_message(264, 'Cannot create class: Max class size should be between 1-10 students.'))
        return [iuser, imagic, response]

    class_id = do_database_execute(
        f'Insert into class (trainerid, skillid, start, max, note) VALUES ({iuser},{skill_id},{start_date},{max_students},"{note}")',
        get_primary_key=True)
    class_size = 0

    response.append(
        build_response_class(class_id, skill_name, trainer_name, start_date, note, class_size, max_students, 'edit'))
    response.append(build_response_redirect(f"/class/{class_id}"))
    response.append(build_response_message(0, "Successfully created class."))
    return [iuser, imagic, response]


# HTTPRequestHandler class
class myHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    # POST This function responds to GET requests to the web server.
    def do_POST(self):

        # The set_cookies function adds/updates two cookies returned with a webpage.
        # These identify the user who is logged in. The first parameter identifies the user
        # and the second should be used to verify the login session.
        def set_cookies(x, user, magic):
            ucookie = Cookie.SimpleCookie()
            ucookie['u_cookie'] = user
            x.send_header("Set-Cookie", ucookie.output(header='', sep=''))
            mcookie = Cookie.SimpleCookie()
            mcookie['m_cookie'] = magic
            x.send_header("Set-Cookie", mcookie.output(header='', sep=''))

        # The get_cookies function returns the values of the user and magic cookies if they exist
        # it returns empty strings if they do not.
        def get_cookies(source):
            rcookies = Cookie.SimpleCookie(source.headers.get('Cookie'))
            user = ''
            magic = ''
            for keyc, valuec in rcookies.items():
                if keyc == 'u_cookie':
                    user = valuec.value
                if keyc == 'm_cookie':
                    magic = valuec.value
            return [user, magic]

        # Fetch the cookies that arrived with the GET request
        # The identify the user session.
        user_magic = get_cookies(self)

        print(user_magic)

        # Parse the GET request to identify the file requested and the parameters
        parsed_path = urllib.parse.urlparse(self.path)

        # Decided what to do based on the file requested.

        # The special file 'action' is not a real file, it indicates an action
        # we wish the server to execute.
        if parsed_path.path == '/action':
            self.send_response(200)  # respond that this is a valid page request

            # extract the content from the POST request.
            # This are passed to the handlers.
            length = int(self.headers.get('Content-Length'))
            scontent = self.rfile.read(length).decode('ascii')
            print(scontent)
            if length > 0:
                content = json.loads(scontent)
            else:
                content = []

            # deal with get parameters
            parameters = urllib.parse.parse_qs(parsed_path.query)

            if 'command' in parameters:
                # check if one of the parameters was 'command'
                # If it is, identify which command and call the appropriate handler function.
                # You should not need to change this code.
                if parameters['command'][0] == 'login':
                    [user, magic, response] = handle_login_request(user_magic[0], user_magic[1], content)
                    # The result of a login attempt will be to set the cookies to identify the session.
                    set_cookies(self, user, magic)
                elif parameters['command'][0] == 'logout':
                    [user, magic, response] = handle_logout_request(user_magic[0], user_magic[1], parameters)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'get_my_skills':
                    [user, magic, response] = handle_get_my_skills_request(user_magic[0], user_magic[1])
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')

                elif parameters['command'][0] == 'get_upcoming':
                    [user, magic, response] = handle_get_upcoming_request(user_magic[0], user_magic[1])
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'join_class':
                    [user, magic, response] = handle_join_class_request(user_magic[0], user_magic[1], content)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'leave_class':
                    [user, magic, response] = handle_leave_class_request(user_magic[0], user_magic[1], content)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')

                elif parameters['command'][0] == 'get_class':
                    [user, magic, response] = handle_get_class_detail_request(user_magic[0], user_magic[1], content)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')

                elif parameters['command'][0] == 'update_attendee':
                    [user, magic, response] = handle_update_attendee_request(user_magic[0], user_magic[1], content)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')

                elif parameters['command'][0] == 'cancel_class':
                    [user, magic, response] = handle_cancel_class_request(user_magic[0], user_magic[1], content)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')

                elif parameters['command'][0] == 'create_class':
                    [user, magic, response] = handle_create_class_request(user_magic[0], user_magic[1], content)
                    if user == '!':  # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                else:
                    # The command was not recognised, report that to the user. This uses a special error code that is not part of the codes you will use.
                    response = []
                    response.append(build_response_message(901, 'Internal Error: Command not recognised.'))

            else:
                # There was no command present, report that to the user. This uses a special error code that is not part of the codes you will use.
                response = []
                response.append(build_response_message(902, 'Internal Error: Command not found.'))

            text = json.dumps(response)
            print(text)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(text, 'utf-8'))

        else:
            # A file that does n't fit one of the patterns above was requested.
            self.send_response(404)  # a file not found html response
            self.end_headers()
        return

    # GET This function responds to GET requests to the web server.
    # You should not need to change this function.
    def do_GET(self):

        # Parse the GET request to identify the file requested and the parameters
        parsed_path = urllib.parse.urlparse(self.path)

        # Decided what to do based on the file requested.

        # Return a CSS (Cascading Style Sheet) file.
        # These tell the web client how the page should appear.
        if self.path.startswith('/css'):
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            with open('.' + self.path, 'rb') as file:
                self.wfile.write(file.read())

        # Return a Javascript file.
        # These contain code that the web client can execute.
        elif self.path.startswith('/js'):
            self.send_response(200)
            self.send_header('Content-type', 'text/js')
            self.end_headers()
            with open('.' + self.path, 'rb') as file:
                self.wfile.write(file.read())

        # A special case of '/' means return the index.html (homepage)
        # of a website
        elif parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('./pages/index.html', 'rb') as file:
                self.wfile.write(file.read())

        # Pages of the form /create/... will return the file create.html as content
        # The ... will be a class id
        elif parsed_path.path.startswith('/class/'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('./pages/class.html', 'rb') as file:
                self.wfile.write(file.read())

        # Pages of the form /create/... will return the file create.html as content
        # The ... will be a skill id
        elif parsed_path.path.startswith('/create/'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('./pages/create.html', 'rb') as file:
                self.wfile.write(file.read())

        # Return html pages.
        elif parsed_path.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('./pages' + parsed_path.path, 'rb') as file:
                self.wfile.write(file.read())
        else:
            # A file that does n't fit one of the patterns above was requested.
            self.send_response(404)
            self.end_headers()

        return


def run():
    """This is the entry point function to this code."""
    print('starting server...')
    ## You can add any extra start up code here
    # Server settings
    # When testing you should supply a command line argument in the 8081+ range
    # Changing code below this line may break the test environment. There is no good reason to do so.
    if (len(sys.argv) < 2):  # Check we were given both the script name and a port number
        print("Port argument not provided.")
        return
    server_address = ('127.0.0.1', int(sys.argv[1]))
    httpd = HTTPServer(server_address, myHTTPServer_RequestHandler)
    print('running server on port =', sys.argv[1], '...')
    httpd.serve_forever()  # This function will not return till the server is aborted


run()
