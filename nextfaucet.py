#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# NEXTFAUCET AUTO BOT - RENDER COMPATIBLE (cookies.txt)

import os
import re
import sys
import time
import json
import uuid
import base64
import random
import hashlib
import requests
import numpy as np
import cv2
import warnings
from datetime import datetime
from io import BytesIO
from PIL import Image
import urllib3

# Suppress warnings
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

# ================= CONFIG =================
BASE_URL = "https://nextfaucet.com"
DASHBOARD = f"{BASE_URL}/dashboard.php"
CAPTCHA_REQUEST = f"{BASE_URL}/captcha-request.php"
CONFIG_FILE = "nextfaucet_config.json"
COOKIE_FILE = "cookies.txt"  # <-- cookies.txt se read karega

# ================= COLORS =================
W = "\033[0m"
R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
M = "\033[95m"
B = "\033[1m"
D = "\033[2m"

# ================= COOKIE LOADER =================
def load_cookie_from_file():
    """Load cookie from cookies.txt file"""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            cookie = f.read().strip()
            if cookie:
                return cookie
    
    # Fallback to environment variable
    return os.environ.get("NEXTFAUCET_COOKIE", "")

def get_user_agent():
    """Get user agent from file or env or default"""
    ua_file = "user_agent.txt"
    if os.path.exists(ua_file):
        with open(ua_file, 'r') as f:
            ua = f.read().strip()
            if ua:
                return ua
    
    return os.environ.get("NEXTFAUCET_UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")

# ================= SESSION =================
session = requests.Session()
session.verify = False

# Increase timeout and retry
session.mount('https://', requests.adapters.HTTPAdapter(
    max_retries=3,
    pool_connections=10,
    pool_maxsize=10
))

base_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "sec-ch-ua-mobile": "?1",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "upgrade-insecure-requests": "1",
    "cache-control": "max-age=0"
}
session.headers.update(base_headers)

# ================= UI FUNCTIONS =================
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def clear_line():
    sys.stdout.write("\033[2K\r")
    sys.stdout.flush()

def log(text, color=W, bold=False):
    now = datetime.now().strftime("%H:%M:%S")
    prefix = f"{B if bold else ''}{color}[{now}]{W}"
    print(f"{prefix} {text}")

def temp(text, color=W):
    clear_line()
    now = datetime.now().strftime("%H:%M:%S")
    sys.stdout.write(f"{B}{color}[{now}] {text}{W}")
    sys.stdout.flush()

def banner():
    print(f"{C}╔════════════════════════════════════════════════════════════════╗{W}")
    print(f"{C}║         NEXTFAUCET AUTO BOT v6.0 - RENDER EDITION             ║{W}")
    print(f"{C}║                   cookies.txt Auto Load                        ║{W}")
    print(f"{C}╚════════════════════════════════════════════════════════════════╝{W}")

def print_separator():
    print(f"{D}────────────────────────────────────────────────────────────────{W}")

# ================= COOKIE PARSER =================
def parse_cookie(cookie_string):
    """Parse cookie string and return dict"""
    cookies = {}
    if not cookie_string:
        return cookies
    
    cookie_string = cookie_string.strip()
    
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                cookies[key] = value
    
    return cookies

# ================= CONFIG MANAGER =================
class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    if "stats" not in config:
                        config["stats"] = {}
                    if "total_claims" not in config["stats"]:
                        config["stats"]["total_claims"] = 0
                    if "total_earned" not in config["stats"]:
                        config["stats"]["total_earned"] = 0.0
                    if "success_count" not in config["stats"]:
                        config["stats"]["success_count"] = 0
                    if "fail_count" not in config["stats"]:
                        config["stats"]["fail_count"] = 0
                    return config
            except:
                return self.default_config()
        return self.default_config()
    
    def default_config(self):
        return {
            "clicks": 0,
            "pops": 0,
            "fingerprint": None,
            "cookie_dict": {},
            "cookie_string": None,
            "user_agent": None,
            "stats": {
                "total_claims": 0,
                "total_earned": 0.0,
                "success_count": 0,
                "fail_count": 0
            }
        }
    
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def update_clicks(self):
        self.config["clicks"] = self.config.get("clicks", 0) + 1
        self.save_config()
        return self.config["clicks"]
    
    def update_pops(self):
        self.config["pops"] = self.config.get("pops", 0) + 1
        self.save_config()
        return self.config["pops"]
    
    def get_fingerprint(self, user_agent):
        if self.config.get("fingerprint"):
            return self.config["fingerprint"]
        
        fingerprint_data = [
            user_agent,
            f"{random.randint(1000, 1400)}x{random.randint(2000, 2400)}x24",
            "3", "0", "8", "Linux armv8l", "10",
            random.randbytes(16).hex(),
            "Adreno (TM) 740"
        ]
        fingerprint = hashlib.sha256("||".join(fingerprint_data).encode()).hexdigest()
        self.config["fingerprint"] = fingerprint
        self.save_config()
        return fingerprint
    
    def update_stats(self, earned=0, success=True):
        if success:
            self.config["stats"]["total_claims"] = self.config["stats"].get("total_claims", 0) + 1
            self.config["stats"]["total_earned"] = self.config["stats"].get("total_earned", 0) + earned
            self.config["stats"]["success_count"] = self.config["stats"].get("success_count", 0) + 1
        else:
            self.config["stats"]["fail_count"] = self.config["stats"].get("fail_count", 0) + 1
        self.save_config()

# [Rest of your existing classes - IconCaptchaSolver and NextFaucetBot remain exactly the same]
# ... (paste your IconCaptchaSolver class here)
# ... (paste your NextFaucetBot class here)

# ================= MODIFIED MAIN FOR RENDER =================
def main():
    clear()
    banner()
    
    # Load cookie from cookies.txt
    cookie = load_cookie_from_file()
    
    if not cookie:
        log("ERROR: No cookie found!", R)
        log("Please create cookies.txt file or set NEXTFAUCET_COOKIE env variable", Y)
        log("Format: PHPSESSID=xxx; _uclicks=xxx; popFires=xxx", Y)
        sys.exit(1)
    
    user_agent = get_user_agent()
    
    log(f"Cookie loaded from file", G)
    log(f"User Agent: {user_agent[:50]}...", C)
    
    try:
        bot = NextFaucetBot(cookie, user_agent)
    except ValueError as e:
        log(f"Error: {e}", R)
        sys.exit(1)
    
    if not bot.login_check():
        log("Login failed! Check your cookie format.", R)
        sys.exit(1)
    
    bot.get_account_info()
    log("Bot started successfully!", G)
    print_dashboard(bot)
    
    cycle = 1
    
    while True:
        try:
            log(f"╔══ CYCLE {cycle} ══", C, bold=True)
            
            start_balance = bot.balance
            
            run_claim(bot, bot.claim_faucet, "FAUCET", 3)
            time.sleep(random.uniform(3, 5))
            
            run_claim(bot, bot.claim_scratch, "SCRATCH", 3)
            time.sleep(random.uniform(3, 5))
            
            run_claim(bot, bot.claim_slots, "SLOTS", 3)
            
            bot.get_account_info()
            earned = bot.balance - start_balance
            
            print_separator()
            print(f"  {C}▶ Cycle {cycle} Summary{W}")
            print(f"  {G}►{W} Earned    : {Y}{earned:.8f} BCH{W}")
            print(f"  {G}►{W} Balance   : {Y}{bot.balance:.8f} BCH{W}")
            print(f"  {G}►{W} Level     : {Y}{bot.level}{W}")
            print_separator()
            
            cycle += 1
            
            wait = random.randint(30, 60)
            log(f"Waiting {wait}s before next cycle...", C)
            
            for i in range(wait, 0, -1):
                if i % 10 == 0 or i <= 5:
                    temp(f"  Next cycle in {i:02d}s", C)
                time.sleep(1)
            clear_line()
            
        except KeyboardInterrupt:
            log("\nStopped by user", R)
            bot.config_manager.save_config()
            print_dashboard(bot)
            sys.exit(0)
        except Exception as e:
            log(f"Error: {e}", R)
            time.sleep(30)

def run_claim(bot, claim_func, name, max_retries=3):
    for attempt in range(max_retries):
        result = claim_func()
        
        if result is True:
            if attempt > 0:
                log(f"  ✓ {name} recovered", G)
            return True
        elif result is False:
            if attempt < max_retries - 1:
                wait = min(5 + attempt * 2, 15)
                log(f"  ⟳ Retry {name} in {wait}s", Y)
                time.sleep(wait)
        else:
            return None
    
    return False

def print_dashboard(bot):
    print_separator()
    print(f"  {G}►{W} Script      : {C}NextFaucet Bot v6.0{W}")
    print(f"  {G}►{W} Balance    : {Y}{bot.balance:.8f} BCH{W}")
    print(f"  {G}►{W} Level      : {Y}{bot.level}{W}")
    print(f"  {G}►{W} Claims     : {Y}{bot.claim_count}{W}")
    print(f"  {G}►{W} Total Earned: {Y}{bot.total_earned:.8f} BCH{W}")
    print_separator()

if __name__ == "__main__":
    main()
