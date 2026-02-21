import sys
import os
import json
import urllib.request
import urllib.parse
import re
import webbrowser
import time
import shutil
import html
import termios

def get_login_information():
    with open("/Users/aotyam/Documents/GitHub/aac/test/.aac/login_information.json", "r") as f:
        login_information = json.load(f)
    return login_information

def get_contest_information():
    with open(".aac/contest_information.json", "r") as f:
        contest_information = json.load(f)
    return contest_information

def open_url(url):
    login_information = get_login_information()
    request = urllib.request.Request(url)
    request.add_header("Cookie", "REVEL_SESSION=" + login_information["revel_session"])
    with urllib.request.urlopen(request) as response:
        print("【", response.status, "】Accessed URL: ", url, sep="")
        html = response.read().decode("utf-8")
    return html

def login_atcoder():
    revel_session = input("REVEL_SESSION: ")
    csrf_token = re.search(r"csrf_token:(.+?)\0", urllib.parse.unquote(revel_session)).group(1)
    login_information = {
        "is_login" : True,
        "revel_session" : revel_session,
        "csrf_token" : csrf_token
    }
    with open("/Users/aotyam/Documents/GitHub/aac/test/.aac/login_information.json", "w") as f:
        json.dump(login_information, f, indent=4)

def make_contest(contest_id):
    os.mkdir(contest_id)
    os.chdir(contest_id)
    os.mkdir("bin")
    os.mkdir("in")
    os.mkdir("out")
    os.mkdir("user_out")
    os.mkdir(".aac")
    os.chdir(".aac")
    contest_information = {
        "contest_id" : contest_id,
        "url": "https://atcoder.jp/contests/" + contest_id,
        "tasks": {}
    }
    with open("contest_information.json", "w") as f:
        json.dump(contest_information, f, indent=4)
    os.chdir("../..")

def download_task():
    login_information = get_login_information()
    contest_information = get_contest_information()
    request = urllib.request.Request(contest_information["url"] + "/tasks")
    request.add_header("Cookie", "REVEL_SESSION=" + login_information["revel_session"])
    tasks = open_url(contest_information["url"] + "/tasks")
    for url, id in re.findall(r'<td class="text-center no-break"><a href="([^"]+)">([^<]+)</a></td>', tasks):
        time.sleep(1)
        url = "https://atcoder.jp" + url
        name = url.split("/")[-1]
        contest_information["tasks"][id] = {
            "url": url,
            "name": name,
            "status": "WJ",
            "time": -1
        }
        shutil.copy("/Users/aotyam/Documents/atcoder/template.cpp", id + ".cpp")
        os.mkdir("in/" + id)
        os.mkdir("out/" + id)
        os.mkdir("user_out/" + id)
        request = urllib.request.Request(url)
        request.add_header("Cookie", "REVEL_SESSION=" + login_information["revel_session"])
        cases = open_url(url)
        for case_id, case_input, case_output in re.findall('<h3>入力例 (\d+)</h3>\s*<pre>\s*([^<]*)</pre>.*?<h3>出力例 \d+</h3>\s*<pre>([^<]*)</pre>', cases, re.DOTALL):
            with open("in/" + id + "/" + case_id + ".txt", "w") as f:
                f.write(html.unescape(case_input))
            with open("out/" + id + "/" + case_id + ".txt", "w") as f:
                f.write(html.unescape(case_output))
        webbrowser.open(url)
    with open(".aac/contest_information.json", "w") as f:
        json.dump(contest_information, f, indent=4)

def test_answer(task_id):
    contest_information = get_contest_information()
    contest_information["tasks"][task_id]["time"] = os.path.getmtime(task_id + ".cpp")
    os.system("g++ -std=gnu++23 -I/opt/homebrew/include -o bin/" + task_id + " " + task_id + ".cpp")
    contest_information["tasks"][task_id]["status"] = "AC"
    for case_id in os.listdir("in/" + task_id):
        os.system("bin/" + task_id + " < in/" + task_id + "/" + case_id + " > user_out/" + task_id + "/" + case_id)
        with open("user_out/" + task_id + "/" + case_id, "r") as f:
            user_output = f.read().strip()
        with open("out/" + task_id + "/" + case_id, "r") as f:
            case_output = f.read().strip()
        with open("in/" + task_id + "/" + case_id, "r") as f:
            case_input = f.read().strip()
        if user_output == case_output:
            print(case_id, "\033[42m AC \033[0m")
        else:
            print(case_id, "\033[41m WA \033[0m")
            print("---- case input ----")
            print(case_input)
            print("---- case output ----")
            print(case_output)
            print("---- your output ----")
            print(user_output)
            print()
            contest_information["tasks"][task_id]["status"] = "WA"
    with open(".aac/contest_information.json", "w") as f:
        json.dump(contest_information, f, indent=4)

def submit_answer(task_id):
    login_information = get_login_information()
    contest_information = get_contest_information()
    if contest_information["tasks"][task_id]["status"] != "AC" or contest_information["tasks"][task_id]["time"] != os.path.getmtime(task_id + ".cpp"):
        test_answer(task_id)
    if contest_information["tasks"][task_id]["status"] != "AC":
        return
    url = contest_information["url"] + "/submit"
    request = urllib.request.Request(url)
    request.add_header("Cookie", "REVEL_SESSION=" + login_information["revel_session"])
    data = {
        "data.TaskScreenName": contest_information["tasks"][task_id]["name"],
        "data.LanguageId": "6017",
        "sourceCode": open(task_id + ".cpp", "r").read(),
        "csrf_token": login_information["csrf_token"]
    }
    data = urllib.parse.urlencode(data).encode("utf-8")
    with urllib.request.urlopen(request, data) as response:
        print(response.status)
        submissions = response.read().decode("utf-8")
    url = contest_information["url"] + re.search(r'/submissions/\d+', contest_information["url"]).group()
    request = urllib.request.Request(url)
    request.add_header("Cookie", "REVEL_SESSION=" + login_information["revel_session"])
    time.sleep(1)
    while True:
        with urllib.request.urlopen(request) as response:
            submission = response.read().decode("utf-8")
        status = re.search(r'<td id="judge-status"[^>]*>\s*<span[^>]*>([^<]+)</span>\s*</td>', submission).group(1)
        if  status == "WJ" or "/" in status:
            print("\r\033[47m" + status + "\033[0m", end="")
        elif status == "AC":
            print("\r\033[42mAC\033[0m")
            break
        else:
            print("\r\033[43m" + status + "\033[0m")
            break
        time.sleep(2)

try:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new_settings = termios.tcgetattr(fd)
    new_settings[3] = new_settings[3] & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
    argv = []
    optv = []
    for arg in sys.argv:
        if arg[0] == "-":
            optv.append(arg)
        else:
            argv.append(arg)
    if argv[1] in ("li", "login"):
        login_atcoder()
    elif argv[1] in ("m", "mk", "make"):
        make_contest(argv[2])
    elif argv[1] in ("d", "dl", "download"):
        download_task()
    elif argv[1] in ("t", "ts", "test"):
        test_answer(argv[2])
    elif argv[1] in ("s", "sm", "submit"):
        submit_answer(argv[2])
finally:
    termios.tcflush(fd, termios.TCIFLUSH)
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)