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
import string
from http.server import BaseHTTPRequestHandler, HTTPServer  # the heavy lifting of the web server
import urllib  # some url parsing support
import json  # support for json encoding
import sys  # needed for agument handling
import time  # time support

import base64  # some encoding support
import sqlite3  # sql database
import random  # generate random numbers
import time  # needed to record when stuff happened
import datetime

import numpy
import numpy as np

def random_digits(n):
    """This function provides a random integer with the specfied number of digits and no leading zeros."""
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return random.randint(range_start, range_end)


# The following three functions issue SQL queries to the database.

def do_database_execute(op):
    """Execute an sqlite3 SQL query to database.db that does not expect a response."""
    print(op)
    try:
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute(op)
        db.commit()
    except Exception as e:
        db.rollback()
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

def check_if_session_invalid(imagic, iuser):
    return do_database_fetchone(f'SELECT magic FROM session WHERE userid = {iuser}')[0] == imagic

def check_username_in_database(username):
    res = do_database_fetchone(f'SELECT * FROM users WHERE username = "{username}"')
    return bool(res)

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
    if not check_username_in_database(username):
        response.append(build_response_message(200, 'Username: ' + username + ' does not exist.'))
        return [iuser, imagic, response]
    if not check_password_for_username(username, password):
        response.append(build_response_message(201, 'Incorrect password.'))
        return [iuser, imagic, response]
    imagic = random_digits(10)
    iuser = do_database_fetchone(f'SELECT userid FROM users WHERE username = "{username}"')[0]
    # Todo: it is not logging out previous sessions even though the session table updates here, it doesnt seem to update all together.
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
    check_session = check_if_session_invalid(imagic, iuser)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    response.append({"type": "redirect", "where": "\logout.html"})
    return [iuser, imagic, response]

def format_my_returns(tuple_in):
    out = []
    for val in tuple_in:
        out.append(val[0])
    return tuple(out)

def get_skills_where_user_is_trainer_and_clean_array(my_skills, user_is_trainer):
    for arr in user_is_trainer:
        trainer_id = arr[0]
        skill_id = arr[1]
        skill_name = do_database_fetchone(f'SELECT name FROM skill WHERE skillid = {skill_id}')[0]
        trainer_name = do_database_fetchone(f'SELECT fullname FROM users WHERE userid = {trainer_id}')[0]
        gained = None
        status = "trainer"
        my_skills = numpy.append(my_skills, [[skill_id, skill_name, trainer_name, gained, status]], axis=0)
    indices_to_delete = []
    for i, row in enumerate(my_skills):
        if row[4] in ["cancelled", "removed"]:
            indices_to_delete.append(i)
        elif row[4] == 'enrolled':
            if int(row[3]) < int(time.time()):
                my_skills[i][4] = "scheduled"
            elif int(row[3]) >= int(time.time()):
                my_skills[i][4] = "pending"
    my_skills = np.delete(my_skills, indices_to_delete, axis=0)
    return my_skills

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
        return do_database_fetchone(f'SELECT fullname FROM users WHERE userid = {trainer_ids}')[0]
    trainer_names = []
    for id in trainer_ids:
        name = do_database_fetchone(f'SELECT fullname FROM users WHERE userid = {id}')
        if name:
            trainer_names.append(name[0])
    return trainer_names

def get_skill_names(skill_ids):
    if isinstance(skill_ids, int):
        return do_database_fetchone(f'SELECT name FROM skill WHERE skillid = {skill_ids}')[0]
    skills = []
    for val in skill_ids:
        skill = do_database_fetchone(f'SELECT name FROM skill WHERE skillid = {val}')
        if skill:
            skills.append(skill[0])
    return skills

def get_skillids_trainerids_start(class_ids):
    skill_ids = []
    trainer_ids = []
    start_dates = []
    for id in class_ids:
        out = do_database_fetchone(f'SELECT skillid, trainerid, start FROM class WHERE classid = {id}')
        if out:
            skill_ids.append(out[0])
            trainer_ids.append(out[1])
            start_dates.append(out[2])
    return skill_ids, start_dates, trainer_ids

def get_my_skills_array(class_ids, statuses):
    my_skills = []

    skill_ids, start_dates, trainer_ids = get_skillids_trainerids_start(class_ids)
    my_skills.append(skill_ids)

    skills = get_skill_names(skill_ids)
    my_skills.append(skills)

    trainer_names = get_trainer_names(trainer_ids)
    my_skills.append(trainer_names)

    my_skills.append(start_dates)

    states = get_states_of_users(statuses)
    my_skills.append(states)

    my_skills = np.array(my_skills).transpose()
    user_is_trainer = do_database_fetchall(f'SELECT trainerid, skillid FROM trainer WHERE trainerid = 1')

    my_skills = get_skills_where_user_is_trainer_and_clean_array(my_skills, user_is_trainer)

    return my_skills

def handle_get_my_skills_request(iuser, imagic):
    """This code handles a request for a list of a users skills.
       You must return a value for all vehicle types, even when it's zero."""

    response = []
    print(iuser, imagic)
    check_session = check_if_session_invalid(imagic, iuser)
    print(check_session)
    if not check_session:
        response.append({"type": "redirect", "where": "/login.html"})
        return [iuser, imagic, response]

    class_ids = format_my_returns(do_database_fetchall(f'SELECT classid FROM attendee WHERE userid = {iuser}'))
    statuses = format_my_returns(do_database_fetchall(f'SELECT status FROM attendee WHERE userid = {iuser}'))
    my_skills = get_my_skills_array(class_ids, statuses)
    for row in my_skills:
        dic = {
            "type": "skill",
            "id": row[0],
            "name": row[1],
            "trainer": row[2],
            "gained": row[3],
            "state": row[4]
        }
        response.append(dic)

    # Todo: CHECK FORUM, is the trainer in the class?
    return [iuser, imagic, response]

def handle_get_upcoming_request(iuser, imagic):
    """This code handles a request for the details of a class.
       """

    response = []

    ## Add code here

    return [iuser, imagic, response]

def handle_get_class_detail_request(iuser, imagic, content):
    """This code handles a request for a list of upcoming classes.
       """

    response = []

    ## Add code here

    return [iuser, imagic, response]


def handle_join_class_request(iuser, imagic, content):
    """This code handles a request by a user to join a class.
      """
    response = []

    ## Add code here

    return [iuser, imagic, response]


def handle_leave_class_request(iuser, imagic, content):
    """This code handles a request by a user to leave a class.
    """
    response = []

    ## Add code here

    return [iuser, imagic, response]


def handle_cancel_class_request(iuser, imagic, content):
    """This code handles a request to cancel an entire class."""

    response = []

    ## Add code here

    return [iuser, imagic, response]


def handle_update_attendee_request(iuser, imagic, content):
    """This code handles a request to cancel a user attendance at a class by a trainer"""

    response = []
    ## Add code here

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

    skill_name = get_skill_names(skill_id)
    trainer_name = get_trainer_names(iuser)

    try:
        date_time = int(datetime.datetime(year, month, day, hour, minute).timestamp())
        print("Datetime created:", date_time)
    except ValueError as e:
        response.append(build_response_message(204, 'Invalid Date or Time.'))
        return [iuser, imagic, response]

    if max_students > 10 or max_students < 1:
        response.append(build_response_message(205, 'Max class size should be between 1-10 students.'))

    # Todo: Get actual size of class which is the number of student currently on the class
    size = 1
    # Todo: add new class into class table, if trainer in the attendee table, add there as well.
    # Todo: check response, the action bit?
    response.append({"type": "class", "id": skill_id, "name": skill_name, "trainer": trainer_name, "notes": note, "when": date_time, "size": size, "max": max_students, "action": "edit"})
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



## SQL QUERIES

('INSERT into attendee (userid, classid, status) VALUES (1,1,0), '
 '(1,2,1),'
 ' (1,3,2), '
 '(2,2,3), '
 '(2,1,4), '
 '(2,3,1)')

'INSERT into class (trainerid, skillid, start, "max", note) VALUES (1,1,1234567,10,"STFDS"), (1,1,1234578,20,"Applied DataScience"), (2,2,1234589,25, "Stats")'

'INSERT into skill (name) VALUES ("Python"), ("Statistics and Probability")'

'INSERT into trainer values (1,1),(2,2)'

