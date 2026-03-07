#!/usr/bin/env python3
import sys
import pickle
import urllib.request
import urllib.parse
import re
import webbrowser
import time
import shutil
import html
import subprocess
import argparse
from pathlib import Path
from getpass import getpass
import math
import os

# constants
STATUS_COLOR = {
    "AC" : "\033[1;42m",
    "MLE" : "\033[1;43m",
    "TLE": "\033[1;43m",
    "WA" : "\033[1;41m",
    "OLE" : "\033[1;43m",
    "RE" : "\033[1;43m",
    "CE" : "\033[1;43m"
}
STATUS_PRIORITY = {
    "AC" : 0,
    "MLE": 1,
    "TLE": 2,
    "WA" : 3,
    "OLE" : 4,
    "RE" : 5,
    "CE" : 6
}
SCRIPT_DIR = Path(__file__).resolve().parent
CONTEST_INFO_FILE = Path.cwd() / ".aac" / "contest_information.pkl"

# v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v
# =v=v= BEGIN SETTING =v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=
# v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v

# Compile command for C or C++ (e.g. "gcc", "clang")
COMPILE_CMD = "g++"
# Compile arguments for C or C++ (e.g. optimization level, language standard, include paths)
# -o option should not be included
COMPILE_ARGS = ["-O2", "-std=gnu++23", "-I/opt/homebrew/include"]
# Submission language ID for AtCoder
# Below is a list of C or C++ IDs.
# - 6013 C23 (Clang 21.1.0)
# - 6014 C23 (GCC 14.2.0)
# - 6017 C++23 (GCC 15.2.0)
# - 6054 C++ IOI-Style(GNU++20) (GCC 14.2.0)
# - 6116 C++23 (Clang 21.1.0)
LANG_ID = "6017"
# Template file path
# If it is not set or not exists, it will be created empty cpp file.
TEMPLATE_FILE = Path.home() / "Documents" / "atcoder" / "template.cpp"
# login information file path
# The name should be ".aac_login_info.pkl".
LOGIN_INFO_FILE = SCRIPT_DIR / ".aac_login_info.pkl"

# ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^
# =^=^= END SETTING =^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
# ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^

# variables
login_info = None
contest_info = None

# functions
def print_error(*args, **kwargs):
    print("\033[1;91m[ERROR   _(x.x._)]\033[0m", *args, **kwargs)
    sys.exit(1)

def print_success(*args, **kwargs):
    print("\033[32m[SUCCESS _(*.*._)]\033[0m", *args, **kwargs)

def print_warning(*args, **kwargs):
    print("\033[93m[WARNING _(-.-._)]\033[0m", *args, **kwargs)

def print_info(*args, **kwargs):
    print("\033[34m[INFO    _(+.+._)]\033[0m", *args, **kwargs)

def save_login_info():
    LOGIN_INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOGIN_INFO_FILE, "wb") as f:
        pickle.dump(login_info, f)
    print_success("Saved login information")

def get_login_info():
    global login_info
    if login_info is not None:
        return
    if not LOGIN_INFO_FILE.exists():
        login_info = {
            "is_logged_in": False,
            "revel_session": "",
            "csrf_token": "",
            "usr_screen_name": ""
        }
        save_login_info()
        print_info("Created login information file")
    with open(LOGIN_INFO_FILE, "rb") as f:
        login_info = pickle.load(f)
    print_success("Loaded login information")

def save_contest_info():
    CONTEST_INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEST_INFO_FILE, "wb") as f:
        pickle.dump(contest_info, f)
    print_success("Saved contest information")

def get_contest_info():
    global contest_info
    if contest_info is not None:
        return
    if not CONTEST_INFO_FILE.exists():
        print_error("Missing contest information")
    with open(CONTEST_INFO_FILE, "rb") as f:
        contest_info = pickle.load(f)
    print_success("Loaded contest information")

def open_url(url, data=None):
    get_login_info()
    request = urllib.request.Request(url)
    if login_info["is_logged_in"]:
        request.add_header("Cookie", "REVEL_SESSION=" + login_info["revel_session"])
    with urllib.request.urlopen(request, data) as response:
        print_info("Accessed", url, "-", response.status)
        return response.read().decode("utf-8"), response.status

def copy_template(path):
    if TEMPLATE_FILE.exists():
        shutil.copy(TEMPLATE_FILE, path)
        print_success("Copied template")
    else:
        path.touch()
        print_warning("Template not found")

def compile_answer(task_id):
    global contest_info
    source = Path.cwd() / (task_id + TEMPLATE_FILE.suffix)
    dest = Path.cwd() / ".aac" / "bin" / task_id
    if not source.exists():
        print_error(task_id, "source file not found")
    if (contest_info["tasks"][task_id]["compile_time"] == source.stat().st_mtime and dest.exists()):
        print_info("Skipped compilation")
        return True
    print_info("Compiling", task_id)
    result = subprocess.run([COMPILE_CMD, *COMPILE_ARGS, source.as_posix(), "-o", dest.as_posix()])
    contest_info["tasks"][task_id]["compile_time"] = source.stat().st_mtime
    if result.returncode != 0:
        print_warning("Compilation failed")
        return False
    print_success("Compilation succeeded")
    return True

def compare_output(out_path, usr_out_path):
    if not out_path.exists():
        print_error("Sample output file not found")
    if not usr_out_path.exists():
        print_error("User output file not found")
    with open(out_path, "r") as f_expected, open(usr_out_path, "r") as f_actual:
        expected = f_expected.read().split()
        actual = f_actual.read().split()
    if len(expected) != len(actual):
        return False
    for exp, act in zip(expected, actual):
        if exp == act:
            continue
        try:
            exp_val = float(exp)
            act_val = float(act)
            if not math.isclose(exp_val, act_val, rel_tol=1e-6, abs_tol=1e-6):
                return False
        except ValueError:
            return False
    return True

# comands
def login_atcoder():
    global login_info
    get_login_info()
    if login_info["is_logged_in"]:
        print_info("Already logged in as", login_info["usr_screen_name"])
        return
    login_info["is_logged_in"] = True
    login_info["revel_session"] = getpass("REVEL_SESSION: ").strip()
    html, status = open_url("https://atcoder.jp")
    if "logged_in" not in html:
        print_error("Invalid REVEL_SESSION")
    decoded_revel_session = urllib.parse.unquote(login_info["revel_session"])
    login_info["csrf_token"] = re.search(r"csrf_token:([^\0]+)", decoded_revel_session).group(1)
    login_info["usr_screen_name"] = re.search(r"UserScreenName:([^\0]+)", decoded_revel_session).group(1)
    save_login_info()
    print_success("Logged in as", login_info["usr_screen_name"])

def logout_atcoder():
    get_login_info()
    if not login_info["is_logged_in"]:
        print_info("Already logged out")
        return
    LOGIN_INFO_FILE.unlink()
    print_info("Removed login information file")
    print_success("Logged out")

def make_contest(contest_id):
    global contest_info
    match = re.match("https://atcoder.jp/contests/([^/]+)", contest_id)
    if match is not None:
        contest_id = match.group(1)
        print_info(contest_id, "extracted from URL")
    contest_dir = Path.cwd() / contest_id
    if contest_dir.exists():
        print_error(contest_id, "already exists")
    contest_url = "https://atcoder.jp/contests/" + contest_id
    html, status = open_url(contest_url)
    if status != 200:
        print_error(contest_id, "does not exist")
    contest_dir.mkdir()
    (contest_dir / ".aac").mkdir()
    (contest_dir / ".aac" / "bin").mkdir()
    (contest_dir / "in").mkdir()
    (contest_dir / "out").mkdir()
    (contest_dir / "usr_out").mkdir()
    contest_info = {
        "id": contest_id,
        "url": contest_url,
        "tasks": {}
    }
    with open(contest_dir / ".aac" / "contest_information.pkl", "wb") as f:
        pickle.dump(contest_info, f)
    print_success("Created", contest_id, "directory")

def remove_contest(contest_id):
    contest_dir = Path.cwd() / contest_id
    if not (contest_dir / ".aac" / "contest_information.pkl").exists():
        print_error("Missing contest information")
    shutil.rmtree(contest_dir)
    print_success("Removed", contest_id, "directory")

def download_task():
    global contest_info
    get_login_info()
    get_contest_info()
    contest_tasks_url = contest_info["url"] + "/tasks"
    tasks, status = open_url(contest_tasks_url)
    for i in range(2,11):
        if status == 200:
            break
        print_warning("Failed to access tasks page, retrying... (", i, "/10)", sep="")
        time.sleep(1)
        tasks, status = open_url(contest_tasks_url)
    if status != 200:
        print_error("Failed to access tasks page 10 times")
    print_success("Accessed tasks page")
    for task_url, task_id, task_name, task_time_limit in re.findall(r'<td[^>]*>\s*<a href="([^"]*)">([^<]*)</a>\s*</td>\s*<td[^>]*>\s*<a[^>]*>([^<]*)</a>\s*</td>\s*<td[^>]*>(\S*) sec</td>', tasks):
        print_info("Downloading", task_id, "-", task_name)
        task_url = "https://atcoder.jp" + task_url
        task_name = html.unescape(task_name)
        contest_info["tasks"][task_id] = {
            "id": task_url.split("/")[-1],
            "url": task_url,
            "name": task_name,
            "time_limit": float(task_time_limit),
            "status": None,
            "compile_time": -1,
            "test_time": -1,
            "cases": []
        }
        copy_template(Path.cwd() / (task_id + TEMPLATE_FILE.suffix))
        (Path.cwd() / "in" / task_id).mkdir(exist_ok=True)
        (Path.cwd() / "out" / task_id).mkdir(exist_ok=True)
        (Path.cwd() / "usr_out" / task_id).mkdir(exist_ok=True)
        time.sleep(0.5)
        cases, status = open_url(task_url)
        for case_id, case_in in re.findall('<h3>Sample Input ([^<]+)</h3><pre>([^<]+)</pre>', cases):
            with open(Path.cwd() / "in" / task_id / ("sample_" + case_id + ".txt"), "w") as f:
                f.write(html.unescape(case_in))
            contest_info["tasks"][task_id]["cases"].append("sample_" + case_id + ".txt")
            print_info("Downloaded sample input", case_id)
        for case_id, case_out in re.findall('<h3>Sample Output ([^<]+)</h3><pre>([^<]+)</pre>', cases):
            with open(Path.cwd() / "out" / task_id / ("sample_" + case_id + ".txt"), "w") as f:
                f.write(html.unescape(case_out))
            print_info("Downloaded sample output", case_id)
        time.sleep(0.5)
        webbrowser.open(task_url)
        print_success("Downloaded", task_id, "-", task_name)
    save_contest_info()
    print_success("Downloaded all tasks")

def execute_answer(task_id):
    get_contest_info()
    if task_id not in contest_info["tasks"]:
        print_error("Task ID", task_id, "not found")
    if not compile_answer(task_id):
        print_error("Compile error")
    bin_path = Path.cwd() / ".aac" / "bin" / task_id
    print_info("Executing", task_id)
    subprocess.run([bin_path.as_posix()])
    print()
    print_success("Executed", task_id)

def test_answer(task_id, all_display=False):
    global contest_info
    get_contest_info()
    if task_id not in contest_info["tasks"]:
        print_error("Task ID", task_id, "not found")
    if compile_answer(task_id):
        if contest_info["tasks"][task_id]["test_time"] == contest_info["tasks"][task_id]["compile_time"]:
            print_info("Skipped testing")
        else:
            contest_info["tasks"][task_id]["status"] = "AC"
            contest_info["tasks"][task_id]["test_time"] = contest_info["tasks"][task_id]["compile_time"]
            bin_path = Path.cwd() / ".aac" / "bin" / task_id
            for case in sorted((Path.cwd() / "in" / task_id).glob("sample_*.txt")):
                print_info("Testing", task_id, "-", case.name)
                status = "AC"
                in_path = case
                out_path = Path.cwd() / "out" / task_id / case.name
                usr_out_path = Path.cwd() / "usr_out" / task_id / case.name
                with open(in_path, "r") as f_in, open(usr_out_path, "w") as f_usr_out:
                    try:
                        start_time = time.perf_counter()
                        result = subprocess.run([bin_path.as_posix()],
                                                stdin=f_in,
                                                stdout=f_usr_out,
                                                stderr=subprocess.DEVNULL,
                                                timeout=contest_info["tasks"][task_id]["time_limit"])
                        end_time = time.perf_counter()
                        elapsed_time = end_time - start_time
                        if result.returncode != 0:
                            status = "RE"
                        elif elapsed_time > contest_info["tasks"][task_id]["time_limit"]:
                            status = "TLE"
                    except subprocess.TimeoutExpired:
                        status = "TLE"
                if status == "AC" and not compare_output(out_path, usr_out_path):
                    status = "WA"
                print("Status          :", STATUS_COLOR[status], status, "\033[0m")
                if status == "TLE":
                    print("Time            : >", int(contest_info["tasks"][task_id]["time_limit"]*1000), "ms")
                else:
                    print("Time            : ", int(elapsed_time*1000), "ms")
                if status == "WA" or all_display:
                    print("Input           :")
                    with open(in_path, "r") as f_in:
                        print(f_in.read().strip())
                    print("Expected Output :")
                    with open(out_path, "r") as f_out:
                        print(f_out.read().strip())
                    print("Your Output     :")
                    with open(usr_out_path, "r") as f_usr_out:
                        print(f_usr_out.read().strip())
                print_info("Tested", task_id, "-", case.name)
                if STATUS_PRIORITY[status] > STATUS_PRIORITY[contest_info["tasks"][task_id]["status"]]:
                    contest_info["tasks"][task_id]["status"] = status
    else:
        contest_info["tasks"][task_id]["status"] = "CE"
    print("=-=-= Test result =-=-=-=-=-=-=-=-=-=-=-=-=-=")
    print("Task   :", task_id)
    print("Status :", STATUS_COLOR[contest_info["tasks"][task_id]["status"]], contest_info["tasks"][task_id]["status"], "\033[0m")
    print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    save_contest_info()
    
def submit_answer(task_id, force=False):
    get_login_info()
    get_contest_info()
    if task_id not in contest_info["tasks"]:
        print_error("Task ID", task_id, "not found")
    if not force:
        test_answer(task_id)
    if not force and contest_info["tasks"][task_id]["status"] != "AC":
        print_error("Not AC")
    submit_url = contest_info["url"] + "/submit"
    answer_file = Path.cwd() / (task_id + TEMPLATE_FILE.suffix)
    with open(answer_file, "r") as f:
        answer_code = f.read()
    data = {
        "data.LanguageId": str(LANG_ID),
        "data.TaskScreenName": contest_info["tasks"][task_id]["id"],
        "sourceCode": answer_code,
        "csrf_token": login_info["csrf_token"]
    }
    submissions, status = open_url(submit_url, data=urllib.parse.urlencode(data).encode("utf-8"))
    match = re.search(r'/submissions/\d+', submissions)
    if match is None:
        print_error("Submission failed")
    print_success("Submission succeeded")
    submission_url = "https://atcoder.jp" + match.group()
    while True:
        time.sleep(1)
        submission, status = open_url(submission_url)
        judge_status = re.search(r'judge-status[^>]*>\s*<span[^>]*>([^<]+)', submission)
        if judge_status is None:
            print_error("Failed to get submission status")
        judge_status = judge_status.group(1)
        if re.match(r'WJ|^\d+/\d+$', judge_status):
            print("\033[2Kstatus : \033[47m" + judge_status + "\033[0m", end="\r\033[1A")
            continue
        elif judge_status == "AC":
            print("\033[2Kstatus : \033[42m AC \033[0m")
            break
        else:
            print("\033[2Kstatus :", STATUS_COLOR.get(judge_status, "\033[1;43m"), judge_status, "\033[0m")
            break
    
def main():
    parser = argparse.ArgumentParser(description="AtCoder Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ログイン
    subparsers.add_parser("login", aliases=["li"], help="Login to AtCoder")
    
    # ログアウト
    subparsers.add_parser("logout", aliases=["lo"], help="Logout from AtCoder")
    
    # コンテストディレクトリの作成
    p_make = subparsers.add_parser("make", aliases=["mk", "m"], help="Initialize contest directory")
    p_make.add_argument("contest_id", help="Contest ID (e.g. abc100)")

    # コンテストディレクトリの削除
    p_remove = subparsers.add_parser("remove", aliases=["rm", "r"], help="Remove contest directory")
    p_remove.add_argument("dir", help="Contest directory")

    # タスクのダウンロード
    subparsers.add_parser("download", aliases=["dl", "d"], help="Download tasks")

    # 単体実行
    p_exec = subparsers.add_parser("execute", aliases=["ex", "e"], help="Execute local solution")
    p_exec.add_argument("task_id", help="Task ID (e.g. A, B, C)")

    # テスト
    p_test = subparsers.add_parser("test", aliases=["ts", "t"], help="Test local solution")
    p_test.add_argument("task_id", help="Task ID (e.g. A, B, C)")
    p_test.add_argument("-a", "--all", action="store_true", help="Display all test cases results")

    # 提出
    p_submit = subparsers.add_parser("submit", aliases=["sm", "s"], help="Submit solution")
    p_submit.add_argument("task_id", help="Task ID (e.g. A, B, C)")
    p_submit.add_argument("-f", "--force", action="store_true", help="Submit without testing")

    args = parser.parse_args()
    
    if args.command in ["login", "li"]:
        login_atcoder()
    elif args.command in ["logout", "lo"]:
        logout_atcoder()
    elif args.command in ["make", "mk", "m"]:
        make_contest(args.contest_id)
    elif args.command in ["remove", "rm", "r"]:
        remove_contest(Path(args.dir))
    elif args.command in ["download", "dl", "d"]:
        download_task()
    elif args.command in ["execute", "ex", "e"]:
        execute_answer(args.task_id)
    elif args.command in ["test", "ts", "t"]:
        test_answer(args.task_id, all_display=args.all)
    elif args.command in ["submit", "sm", "s"]:
        submit_answer(args.task_id, force=args.force)
    else:
        print_error("Unknown command")

if __name__ == "__main__":
    main()
