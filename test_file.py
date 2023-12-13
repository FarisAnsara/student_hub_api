
# The modules needed
import random
import requests
import shutil
import json
import subprocess

import os
import socket


# %%
# The core code

def request2server_get(url, cookies):
    """Send a get request to the server"""
    ucookie = cookies[0]
    mcookie = cookies[1]
    try:
        r = requests.get(url, cookies=dict(u_cookie=cookies[0], m_cookie=cookies[1]), timeout=30)
        for c in r.cookies:
            if (c.name == 'u_cookie'):
                ucookie = c.value
            if (c.name == 'm_cookie'):
                mcookie = c.value
        act = json.loads(r.text)
        return [[ucookie, mcookie], act]
    except:
        print("Invalid login")
        return [[ucookie, mcookie], []]


def request2server_post(url, cookies, content):
    """Send a post request to the server"""
    ucookie = cookies[0]
    mcookie = cookies[1]
    try:
        r = requests.post(url, cookies=dict(u_cookie=cookies[0], m_cookie=cookies[1]), json=content, timeout=30)
        for c in r.cookies:
            if (c.name == 'u_cookie'):
                ucookie = c.value
            if (c.name == 'm_cookie'):
                mcookie = c.value
        act = json.loads(r.text)
        return [[ucookie, mcookie], act]
    except:
        print("Invalid login")
        return [[ucookie, mcookie], []]


def do_login(cookies, user, pasw):
    """Send a login command"""
    global server_port
    content = {"command": "login", "username": user, "password": pasw}
    return request2server_post("http://localhost:" + server_port + "/action?command=login", cookies, content)


def do_logout(cookies):
    """Send a logout command"""
    global server_port
    content = {"command": "logout"}
    return request2server_post("http://localhost:" + server_port + "/action?command=logout", cookies, content)


# %%
def find_redirect(act):
    """Check for a redirect response. Return the where target if found or None otherwise."""
    if act == None:
        return None
    try:
        for a in act:
            if (a['type'] == 'redirect'):
                return a['where']
    except:
        return None


def checked_login(test, cookies, user, pasw):
    """Send a login command and check it's good."""
    [cookies, act] = do_login(cookies, user, pasw)
    where = find_redirect(act)
    if (where == None):
        print("Test " + str(test) + " Failed - Expected redirect during login.")
        return ['', act, False]
    if (where != '/index.html'):
        print("Test " + str(test) + " Failed - Expected /index.html got {" + where + "}")
        return [cookies, act, False]
    return [cookies, act, True]


def checked_logout(test, cookies):
    """Send a logout command and check it's good."""
    [cookies, act] = do_logout(cookies)
    where = find_redirect(act)
    if (where == None):
        print("Test " + str(test) + " Failed - Expected redirect during logout.")
        return [cookies, act, False]
    if (where != '/logout.html'):
        print("Test " + str(test) + " Failed - Expected /logout.html got {" + where + "}")
        return [cookies, act, False]
    return [cookies, act, True]


# %%
# Test 1 - Simple login
def test1():
    """Check that login and logout work for a good user."""
    try:
        cookies = ['', '']
        [cookies, act, flag] = checked_login(1, cookies, "test1", "pass1word")
        if flag != True:
            return 0

        [cookies, act, flag] = checked_logout(1, cookies)
        if flag != True:
            return 0

        print("Test 1 Passed")
        return 1
    except:
        print("Test 1 Failed - Exception Caused.")
        return 0


# %%
# The lists of tests, you can add your own here.
# test description, test function, database to use for test
tests = [('Test 1 Simple login test.', test1, 'database.db')
         ]


def test_suite(file_to_run):
    """Iterate over all the tests and run them with a fresh server and copy of the specified database"""
    global server_port  # we cycle through ports if a program fails and occupies the port

    mark_total = 0  # how many tests pass

    # loop over the tests
    for tnumber, test in enumerate(tests, start=1):

        # make sure we are using a free port
        port = int(server_port)
        busy = 1
        while busy == 1:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                print('Port', port, 'busy')
                port += 1
            else:
                print('Using port', port)
                busy = 0

        server_port = str(port)

        print("Running", test[0])

        # try the test, if it generates an exception that is considered a fail.
        try:
            # copy the database to where the server expects it
            shutil.copy(test[2], 'database.db')

            # start the server, the path of the python executable needs to match your installation.
            sp = subprocess.Popen('C:\Program Files\Anaconda3\python.exe ' + file_to_run + ' ' + server_port)

            # run the test and record the mark.
            tmark = test[1]()
            mark_total += tmark

            # close down the server
            print("Test Finished")
            sp.terminate()

        except Exception as err:
            print(err)
            try:
                sp.terminate()
            except:
                pass
            print("Test Process Generated Exception")
        tnumber += 1

    print("Marks = {:d} for regression tests.".format(mark_total))


server_port = 8080
file_to_run = 'server.py'
test_suite(file_to_run)
# %%
