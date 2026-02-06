import requests
import argparse
import sys
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

# --- Colors ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# --- Banner ---
def banner():
    print(f"""{Colors.MAGENTA}{Colors.BOLD}
██╗   ██╗██████╗ ██████╗ ██╗   ██╗████████╗███████╗██████╗ 
██║   ██║██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗
██║   ██║██████╔╝██████╔╝██║   ██║   ██║   █████╗  ██████╔╝
██║   ██║██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  ██╔══██╗
╚██████╔╝██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██║  ██║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝                                                         
    ADVANCED ENUMERATOR (Made by: IanNarito)
{Colors.RESET}""")

# --- User Agents ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

# --- Session ---
def get_session(retries=3):
    session = requests.Session()

    retry_strategy = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429,500,502,503,504]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# --- Username Check ---
def check_username(url, username, success_string, fail_string):
    user = username.strip()

    if not user:
        return None

    session = get_session()

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "username": user,
        "password": "password123"
    }

    try:
        response = session.post(
            url,
            data=data,
            headers=headers,
            timeout=10,
            allow_redirects=False
        )

        text = response.text.lower()

        if success_string and success_string.lower() in text:
            return ("hit", user)

        if fail_string and fail_string.lower() not in text:
            return ("hit", user)

        if response.status_code in [301,302,303,307,308]:
            return ("hit", user)

        if len(response.text) > 5000:
            return ("maybe", user)

    except requests.RequestException:
        return ("error", user)

    return None

# --- Main ---
def main():
    parser = argparse.ArgumentParser(description="Advanced Username Enumerator")

    parser.add_argument("-u","--url",required=True)
    parser.add_argument("-w","--wordlist",required=True)
    parser.add_argument("-t","--threads",type=int,default=20)
    parser.add_argument("-s","--success")
    parser.add_argument("-f","--fail")
    parser.add_argument("-o","--output")

    args = parser.parse_args()

    if not args.success and not args.fail:
        print(f"{Colors.RED}[!] Need success or fail string{Colors.RESET}")
        sys.exit(1)

    banner()

    print(f"{Colors.CYAN}[TARGET]   {args.url}{Colors.RESET}")
    print(f"{Colors.CYAN}[THREADS]  {args.threads}{Colors.RESET}")
    print(f"{Colors.CYAN}[WORDLIST] {args.wordlist}{Colors.RESET}\n")

    try:
        with open(args.wordlist,"r",encoding="utf-8",errors="ignore") as f:
            usernames = f.readlines()
    except:
        print(f"{Colors.RED}[!] Wordlist not found{Colors.RESET}")
        sys.exit(1)

    hits = 0
    errors = 0
    checked = 0
    found_users = []

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:

        futures = {
            executor.submit(
                check_username,
                args.url,
                user,
                args.success,
                args.fail
            ): user for user in usernames
        }

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           unit="req",
                           ncols=90,
                           bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}"):

            checked += 1

            result = future.result()

            if result:

                status, user = result

                if status == "hit":
                    hits += 1
                    found_users.append(user)
                    tqdm.write(f"{Colors.GREEN}[VALID] {user}{Colors.RESET}")

                elif status == "maybe":
                    tqdm.write(f"{Colors.YELLOW}[POSSIBLE] {user}{Colors.RESET}")

                elif status == "error":
                    errors += 1
                    tqdm.write(f"{Colors.RED}[ERROR] {user}{Colors.RESET}")

    duration = round(time.time() - start_time,2)

    print(f"\n{Colors.BOLD}{Colors.BLUE}=== SESSION SUMMARY ==={Colors.RESET}")
    print(f"{Colors.GREEN}Valid Users : {hits}{Colors.RESET}")
    print(f"{Colors.RED}Errors      : {errors}{Colors.RESET}")
    print(f"{Colors.CYAN}Checked     : {checked}{Colors.RESET}")
    print(f"{Colors.MAGENTA}Time Taken  : {duration}s{Colors.RESET}")

    if args.output and found_users:
        with open(args.output,"w") as f:
            for user in found_users:
                f.write(user+"\n")

        print(f"{Colors.GREEN}Saved Results → {args.output}{Colors.RESET}")

    print(f"{Colors.BLUE}[*] Enumeration Complete{Colors.RESET}")

if __name__ == "__main__":
    main()
