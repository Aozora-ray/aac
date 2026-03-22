#!/usr/bin/env python3
import sys
import pickle
import urllib.request
import urllib.parse
import re
import time
import shutil
import html
import subprocess
import argparse
from pathlib import Path
from getpass import getpass
import math
import os
from concurrent.futures import ThreadPoolExecutor

# constants
STATUS_COLOR = {
    "AC" : "\033[38;2;255;255;255;48;2;92;184;92m",
    "MLE" : "\033[38;2;255;255;255;48;2;240;173;78m",
    "TLE": "\033[38;2;255;255;255;48;2;240;173;78m",
    "WA" : "\033[38;2;255;255;255;48;2;240;173;78m",
    "OLE" : "\033[38;2;255;255;255;48;2;240;173;78m",
    "RE" : "\033[38;2;255;255;255;48;2;240;173;78m",
    "CE" : "\033[38;2;255;255;255;48;2;240;173;78m",
    "QLE" : "\033[38;2;255;255;255;48;2;240;173;78m",
    "IE" : "\033[38;2;255;255;255;48;2;77;77;77m",
    "WJ" : "\033[38;2;255;255;255;48;2;77;77;77m",
    "/" : "\033[38;2;255;255;255;48;2;77;77;77m"
}
STATUS_PRIORITY = {
    "CE" : 0,
    "RE" : 1,
    "OLE" : 2,
    "WA" : 3,
    "TLE": 4,
    "MLE": 5,
    "AC" : 6
}
SCRIPT_DIR = Path(__file__).resolve().parent
REL_CONTEST_INFO_FILE = Path(".aac") / "contest_information.pkl"
MAX_RETRY = 10
WORKERS = max(1, os.cpu_count() - 1)

# v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v
# =v=v= BEGIN SETTING =v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=
# v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v=v

# Compile command for C or C++ (e.g. "gcc", "clang")
# -o option should not be included
COMPILE_CMD = ["g++", "-O0", "-std=gnu++23"]
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
TEMPLATE_FILE = SCRIPT_DIR / "template.cpp"
# login information file path
# The name should be ".aac_login_info.pkl".
LOGIN_INFO_FILE = SCRIPT_DIR / ".aac_login_info.pkl"

# ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^
# =^=^= END SETTING =^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
# ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^

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

def print_line():
    print("---------------------------------------------")

def compare_output(out_file, usr_out_file):
    if not out_file.exists():
        print_error("Sample output file not found")
    if not usr_out_file.exists():
        print_error("User output file not found")
    with open(out_file, "r") as f_expected, open(usr_out_file, "r") as f_actual:
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

class AotyamAtCoderCLI:
    def __init__(self):
        self.login_info = None
        self.contest_info = None
        self.has_used_https = False

    # functions
    def init_login_info(self):
        self.login_info = {
                "revel_session": "",
                "csrf_token": "",
                "usr_screen_name": ""
            }
        self.save_login_info()

    def get_login_info(self):
        if not LOGIN_INFO_FILE.exists():
            self.init_login_info()
            print_info("Created login information")
        with open(LOGIN_INFO_FILE, "rb") as f:
            self.login_info = pickle.load(f)
        print_success("Loaded login information")
    
    def save_login_info(self):
        with open(LOGIN_INFO_FILE, "wb") as f:
            pickle.dump(self.login_info, f)
        print_success("Saved login information")
    
    def get_contest_info(self):
        if not self.contest_info_file.exists():
            print_error("Missing contest information")
        with open(self.contest_info_file, "rb") as f:
            self.contest_info = pickle.load(f)
        print_success("Loaded contest information")
    
    def save_contest_info(self):
        with open(self.contest_info_file, "wb") as f:
            pickle.dump(self.contest_info, f)
        print_success("Saved contest information")

    def open_url(self, url, data=None):
        if self.has_used_https:
            time.sleep(1)
        self.has_used_https = True
        request = urllib.request.Request(url)
        request.add_header("Cookie", "REVEL_SESSION=" + self.login_info["revel_session"])
        try:
            with urllib.request.urlopen(request, data) as response:
                html = response.read().decode("utf-8")
                status = response.status
        except urllib.error.HTTPError as e:
            html = e.read().decode("utf-8")
            status = e.code
        print_info("Accessed", url, "-", status)
        return html, status
    
    def compile_answer(self, task_id):
        answer_file = Path(task_id + TEMPLATE_FILE.suffix)
        bin_file= Path(".aac") / "bin" / task_id
        if (self.contest_info["tasks"][task_id]["compile_time"] == answer_file.stat().st_mtime):
            print_info("Compilation skipped")
            return self.contest_info["tasks"][task_id]["status"] != "CE"
        print_info("Compiling", task_id)
        result = subprocess.run([*COMPILE_CMD, answer_file.as_posix(), "-o", bin_file.as_posix()])
        self.contest_info["tasks"][task_id]["compile_time"] = answer_file.stat().st_mtime
        if result.returncode != 0:
            print_warning("Compilation failed")
            return False
        print_success("Compilation succeeded")
        return True

    # commands    
    def login_atcoder(self, force=False):
        self.get_login_info()
        if self.login_info["revel_session"] != "" and not force:
            print_info("Already logged in as", self.login_info["usr_screen_name"])
            return
        self.login_info["revel_session"] = getpass("REVEL_SESSION: ").strip()
        html, status = self.open_url("https://atcoder.jp")
        if "logged_in" not in html:
            print_error("Invalid REVEL_SESSION")
        decoded_revel_session = urllib.parse.unquote(self.login_info["revel_session"])
        self.login_info["csrf_token"] = re.search(r"csrf_token:([^\0]+)", decoded_revel_session).group(1)
        self.login_info["usr_screen_name"] = re.search(r"UserScreenName:([^\0]+)", decoded_revel_session).group(1)
        self.save_login_info()
        print_success("Logged in as", self.login_info["usr_screen_name"])

    def logout_atcoder(self):
        self.get_login_info()
        if self.login_info["revel_session"] == "":
            print_info("Already logged out")
            return
        self.init_login_info()
        print_success("Logged out")

    def make_contest(self, contest_id, contest_dir=None, force=False):
        self.get_login_info()
        match = re.match("https://atcoder.jp/contests/([^/]+)", contest_id)
        if match is not None:
            contest_id = match.group(1)
            print_info("Extracted", contest_id)
        if contest_dir is None:
            contest_dir = Path(contest_id)
        if contest_dir.exists() and not force:
            print_error(contest_id, "already exists")
        self.contest_info_file = contest_dir / REL_CONTEST_INFO_FILE
        contest_url = "https://atcoder.jp/contests/" + contest_id
        html, status = self.open_url(contest_url)
        if status != 200:
            print_error(contest_id, "is not accessible")
        for dir_name in [".aac/bin", "in", "out", "usr_out"]:
            (contest_dir / dir_name).mkdir(parents=True, exist_ok=True)
        self.contest_info = {
            "id": contest_id,
            "url": contest_url,
            "tasks": {}
        }
        self.save_contest_info()
        print_success("Created", contest_dir)

    def remove_contest(self, contest_dir="."):
        contest_dir = Path(contest_dir)
        if not contest_dir.exists():
            print_error(contest_dir, "does not exist")
        self.contest_info_file = contest_dir / REL_CONTEST_INFO_FILE
        self.get_contest_info()
        shutil.rmtree(contest_dir)
        print_success("Removed", contest_dir)

    def download_task(self, contest_dir="."):
        contest_dir = Path(contest_dir)
        if not contest_dir.exists():
            print_error(contest_dir, "does not exist")
        self.contest_info_file = contest_dir / REL_CONTEST_INFO_FILE
        self.get_login_info()
        self.get_contest_info()
        if self.login_info["revel_session"] == "":
            print_error("Not logged in")
        contest_tasks_url = self.contest_info["url"] + "/tasks"
        tasks, status = self.open_url(contest_tasks_url)
        for i in range(1, MAX_RETRY+1):
            if status == 200:
                break
            print_warning("Failed to access tasks page, retrying... (", i, "/", MAX_RETRY, ")", sep="")
            tasks, status = self.open_url(contest_tasks_url)
        if status != 200:
            print_error("Failed to access tasks page")
        for task_url, task_id, task_name, task_time_limit in re.findall(r'<td[^>]*>\s*<a href="([^"]*)">([^<]*)</a>\s*</td>\s*<td[^>]*>\s*<a[^>]*>([^<]*)</a>\s*</td>\s*<td[^>]*>(\S*) sec</td>', tasks):
            task_url = "https://atcoder.jp" + task_url
            task_name = html.unescape(task_name)
            self.contest_info["tasks"][task_id] = {
                "id": task_url.split("/")[-1],
                "url": task_url,
                "name": task_name,
                "time_limit": int(float(task_time_limit) * 1000),
                "status": None,
                "compile_time": -1,
                "test_time": -1,
                "cases": []
            }
            answer_file = contest_dir / (task_id + TEMPLATE_FILE.suffix)
            if TEMPLATE_FILE.exists():
                shutil.copy(TEMPLATE_FILE, answer_file)
            else:
                answer_file.touch()
                print_warning("Template not found")
            for dir_name in ["in", "out", "usr_out"]:
                (contest_dir / dir_name / task_id).mkdir(exist_ok=True)
            cases, status = self.open_url(task_url)
            for case_id, case_in, case_out in re.findall('Sample Input ([^<]+)</h3>\s*<pre[^>]*>([^<]*)</pre>\s*</section>\s*</div>\s*<div[^>]*>\s*<section[^>]*>\s*<h3[^>]*>Sample Output [^<]+</h3>\s*<pre[^>]*>([^<]*)', cases):
                case_filename = "sample_" + case_id + ".txt"
                with open(contest_dir / "in" / task_id / case_filename, "w") as f:
                    f.write(html.unescape(case_in))
                with open(contest_dir / "out" / task_id / case_filename, "w") as f:
                    f.write(html.unescape(case_out))
                self.contest_info["tasks"][task_id]["cases"].append({
                    "file_name": case_filename,
                    "status": None,
                    "time": -1
                })
            print_success("Downloaded task", task_id, "-", task_name)
        self.save_contest_info()
        print_success("Downloaded contest", self.contest_info["id"])

    def execute_answer(self, task_id):
        self.contest_info_file = REL_CONTEST_INFO_FILE
        self.get_contest_info()
        if task_id not in self.contest_info["tasks"]:
            print_error("Task ID", task_id, "not found")
        if not self.compile_answer(task_id):
            print_error("Compile error")
        bin_path = Path(".aac") / "bin" / task_id
        print_info("Executing", task_id)
        print_line()
        subprocess.run([bin_path.as_posix()])
        print()
        print_line()
        print_success("Executed", task_id)

    def test_answer(self, task_id, all_display=False):
        self.contest_info_file = REL_CONTEST_INFO_FILE
        self.get_contest_info()
        if task_id not in self.contest_info["tasks"]:
            print_error("Task ID", task_id, "not found")
        if self.compile_answer(task_id):
            self.contest_info["tasks"][task_id]["status"] = "AC"
            if self.contest_info["tasks"][task_id]["test_time"] == self.contest_info["tasks"][task_id]["compile_time"]:
                print_info("Testing skipped")
            else:
                self.contest_info["tasks"][task_id]["test_time"] = self.contest_info["tasks"][task_id]["compile_time"]
                bin_file = Path(".aac") / "bin" / task_id
                def test_case(case_info):
                    status = "AC"
                    in_file = Path("in") / task_id / case_info["file_name"]
                    out_file = Path("out") / task_id / case_info["file_name"]
                    usr_out_file = Path("usr_out") / task_id / case_info["file_name"]
                    with open(in_file, "r") as f_in, open(usr_out_file, "w") as f_usr_out:
                        try:
                            start_time = time.perf_counter()
                            result = subprocess.run([bin_file.as_posix()],
                                                    stdin=f_in,
                                                    stdout=f_usr_out,
                                                    stderr=subprocess.DEVNULL,
                                                    timeout=self.contest_info["tasks"][task_id]["time_limit"] / 1000)
                            end_time = time.perf_counter()
                            case_time = int((end_time - start_time) * 1000)
                            if result.returncode != 0:
                                status = "RE"
                        except subprocess.TimeoutExpired:
                            case_time = self.contest_info["tasks"][task_id]["time_limit"]
                            status = "TLE"
                        if case_time > self.contest_info["tasks"][task_id]["time_limit"] and status != "RE":
                            case_time = self.contest_info["tasks"][task_id]["time_limit"]
                            status = "TLE"
                        if status == "AC" and not compare_output(out_file, usr_out_file):
                            status = "WA"
                    return status, case_time
                with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                    case_results = list(executor.map(test_case, self.contest_info["tasks"][task_id]["cases"]))
                for case_info, (status, case_time) in zip(self.contest_info["tasks"][task_id]["cases"], case_results):
                    case_info["status"] = status
                    case_info["time"] = case_time
            for case_info in self.contest_info["tasks"][task_id]["cases"]:
                print_line()
                print("\033[40m Case        \033[0m :", case_info["file_name"])
                if STATUS_PRIORITY[case_info["status"]] < STATUS_PRIORITY[self.contest_info["tasks"][task_id]["status"]]:
                    self.contest_info["tasks"][task_id]["status"] = case_info["status"]
                print("\033[40m Status      \033[0m :", STATUS_COLOR[case_info["status"]], case_info["status"], "\033[0m")
                if case_info["status"] == "TLE":
                    print("\033[40m Time        \033[0m : >", case_info["time"], "ms")
                else:
                    print("\033[40m Time        \033[0m :", case_info["time"], "ms")
                    if case_info["status"] == "WA" or (case_info["status"] == "AC" and all_display):
                        in_file = Path("in") / task_id / case_info["file_name"]
                        out_file = Path("out") / task_id / case_info["file_name"]
                        usr_out_file = Path("usr_out") / task_id / case_info["file_name"]
                        print("\033[40m Input       \033[0m :")
                        with open(in_file, "r") as f:
                            print(f.read().strip())
                        print("\033[40m Output      \033[0m :")
                        with open(out_file, "r") as f:
                            print(f.read().strip())
                        print("\033[40m Your Output \033[0m :")
                        with open(usr_out_file, "r") as f:
                            print(f.read().strip())
            print_line()
        else:
            self.contest_info["tasks"][task_id]["status"] = "CE"
        print("=-=-= Test result =-=-=-=-=-=-=-=-=-=-=-=-=-=")
        print("\033[40m Task        \033[0m :", task_id)
        print("\033[40m Status      \033[0m :", STATUS_COLOR[self.contest_info["tasks"][task_id]["status"]], self.contest_info["tasks"][task_id]["status"], "\033[0m")
        print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
        self.save_contest_info()
    
    def submit_answer(self, task_id, force=False, all_display=False):
        self.contest_info_file = REL_CONTEST_INFO_FILE
        self.get_login_info()
        self.get_contest_info()
        if self.login_info["revel_session"] == "":
            print_error("Not logged in")
        if task_id not in self.contest_info["tasks"]:
            print_error("Task ID", task_id, "not found")
        if not force:
            self.test_answer(task_id, all_display)
            if self.contest_info["tasks"][task_id]["status"] != "AC":
                print_error("Not AC")
        submit_url = self.contest_info["url"] + "/submit"
        answer_file = Path(task_id + TEMPLATE_FILE.suffix)
        with open(answer_file, "r") as f:
            data = {
                "data.LanguageId": LANG_ID,
                "data.TaskScreenName": self.contest_info["tasks"][task_id]["id"],
                "sourceCode": f.read(),
                "csrf_token": self.login_info["csrf_token"]
            }
        submissions, status = self.open_url(submit_url, urllib.parse.urlencode(data).encode("utf-8"))
        match = re.search(r'/submissions/\d+', submissions)
        if match is None:
            print_error("Submission failed")
        print_success("Submission succeeded")
        submission_url = self.contest_info["url"] + match.group()
        while True:
            submission, status = self.open_url(submission_url)
            match = re.search(r'judge-status[^>]*>\s*<span[^>]*>([^<]+)', submission)
            if match is None:
                print_error("Failed to get submission status")
            judge_status = match.group(1)
            for status in STATUS_COLOR.keys():
                if status in judge_status:
                    print("\033[40mStatus \033[0m:", STATUS_COLOR[status], judge_status, "\033[0m", end="", flush=True)
                    break
            if judge_status != "WJ" and "/" not in judge_status:
                print("\r", end="", flush=True)
                break
            for i in range(3):
                time.sleep(1)
                print(".", end="", flush=True)
            print("\r", end="", flush=True)
        print("=-=-= Submit result =-=-=-=-=-=-=-=-=-=-=-=-=")
        print("\033[40mTask   \033[0m:", task_id)
        print("\033[40mStatus \033[0m:", STATUS_COLOR[judge_status], judge_status, "\033[0m")
        print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
            
def main():
    parser = argparse.ArgumentParser(description="AtCoder Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # login
    p_login = subparsers.add_parser("login", aliases=["li"], help="Login to AtCoder")
    p_login.add_argument("-f", "--force", action="store_true", help="Force login")
    # logout
    subparsers.add_parser("logout", aliases=["lo"], help="Logout from AtCoder")
    # make
    p_make = subparsers.add_parser("make", aliases=["mk", "m"], help="Initialize contest directory")
    p_make.add_argument("contest_id", help="Contest ID (e.g. abc100)")
    p_make.add_argument("-o", "--outdir", help="Output directory (default: contest ID)")
    p_make.add_argument("-f", "--force", action="store_true", help="Force initialization")
    # remove
    p_remove = subparsers.add_parser("remove", aliases=["rm", "r"], help="Remove contest directory")
    p_remove.add_argument("contest_dir", nargs="?", default=".", help="Contest directory")
    # download
    p_download = subparsers.add_parser("download", aliases=["dl", "d"], help="Download tasks")
    p_download.add_argument("contest_dir", nargs="?", default=".", help="Contest directory")
    # execute
    p_exec = subparsers.add_parser("execute", aliases=["ex", "e"], help="Execute local solution")
    p_exec.add_argument("task_id", help="Task ID (e.g. A, B, C)")
    # test
    p_test = subparsers.add_parser("test", aliases=["ts", "t"], help="Test local solution")
    p_test.add_argument("task_id", help="Task ID (e.g. A, B, C)")
    p_test.add_argument("-a", "--all", action="store_true", help="Display all test cases results")
    # submit
    p_submit = subparsers.add_parser("submit", aliases=["sm", "s"], help="Submit solution")
    p_submit.add_argument("task_id", help="Task ID (e.g. A, B, C)")
    p_submit.add_argument("-f", "--force", action="store_true", help="Submit without testing")
    p_submit.add_argument("-a", "--all", action="store_true", help="Display all test cases results when testing")

    args = parser.parse_args()
    aac = AotyamAtCoderCLI()
    if args.command in ["login", "li"]:
        aac.login_atcoder(force=args.force)
    elif args.command in ["logout", "lo"]:
        aac.logout_atcoder()
    elif args.command in ["make", "mk", "m"]:
        aac.make_contest(args.contest_id, args.outdir, force=args.force)
    elif args.command in ["remove", "rm", "r"]:
        aac.remove_contest(args.contest_dir)
    elif args.command in ["download", "dl", "d"]:
        aac.download_task(args.contest_dir)
    elif args.command in ["execute", "ex", "e"]:
        aac.execute_answer(args.task_id)
    elif args.command in ["test", "ts", "t"]:
        aac.test_answer(args.task_id, all_display=args.all)
    elif args.command in ["submit", "sm", "s"]:
        aac.submit_answer(args.task_id, force=args.force, all_display=args.all)
    else:
        print_error("Unknown command")

if __name__ == "__main__":
    main()
