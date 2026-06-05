#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🦅 NEXTFAUCET AUTO BOT - FULLY FIXED VERSION

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

# ================= COLORS =================
W = "\033[0m"
R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
M = "\033[95m"
B = "\033[1m"
D = "\033[2m"

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
    print(f"{C}║              NEXTFAUCET AUTO BOT v6.0 - STABLE                 ║{W}")
    print(f"{C}║                   Fully Fixed & Optimized                      ║{W}")
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
                    # Ensure stats has all required keys
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

# ================= ICON CAPTCHA SOLVER =================
class IconCaptchaSolver:
    
    @staticmethod
    def decode_response(response_text):
        """Decode captcha response"""
        text = response_text.strip()
        
        if not text:
            return None
        
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        try:
            padding = 4 - (len(text) % 4)
            if padding != 4:
                text += '=' * padding
            decoded = base64.b64decode(text).decode('utf-8')
            return json.loads(decoded)
        except:
            pass
        
        try:
            return json.loads(text)
        except:
            pass
        
        return None
    
    @staticmethod
    def extract_image_from_challenge(challenge_data):
        """Extract base64 image from challenge data"""
        if isinstance(challenge_data, str):
            return challenge_data
        elif isinstance(challenge_data, dict):
            if 'image' in challenge_data:
                return challenge_data['image']
            if 'data' in challenge_data:
                return challenge_data['data']
        return None
    
    @staticmethod
    def get_image_size(img_b64):
        """Get image dimensions"""
        try:
            if ',' in img_b64:
                img_b64 = img_b64.split(',')[-1]
            img_data = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_data))
            return img.size[0], img.size[1]
        except:
            return 319, 200
    
    @staticmethod
    def solve_icon_captcha(img_b64):
        """Solve icon captcha by finding the odd icon out"""
        try:
            if ',' in img_b64:
                img_b64 = img_b64.split(',')[-1]
            
            img_data = base64.b64decode(img_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            
            if img is None:
                return None
            
            if len(img.shape) == 3 and img.shape[2] == 4:
                b, g, r, a = cv2.split(img)
                alpha = a / 255.0
                white = np.ones_like(b, dtype=np.uint8) * 255
                b = (b * alpha + white * (1 - alpha)).astype(np.uint8)
                g = (g * alpha + white * (1 - alpha)).astype(np.uint8)
                r = (r * alpha + white * (1 - alpha)).astype(np.uint8)
                img = cv2.merge((b, g, r))
            
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            icons = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if 20 < w < 100 and 20 < h < 80:
                    icon_roi = gray[y:y+h, x:x+w]
                    if icon_roi.size > 0:
                        icon_resized = cv2.resize(icon_roi, (40, 40))
                        icons.append((icon_resized, (x, y, w, h)))
            
            if len(icons) >= 2:
                groups = []
                group_boxes = []
                
                for crop_icon, box in icons:
                    placed = False
                    for i, group in enumerate(groups):
                        diff = cv2.absdiff(group[0], crop_icon)
                        score = np.sum(diff)
                        if score < 50000:
                            groups[i].append(crop_icon)
                            group_boxes[i].append(box)
                            placed = True
                            break
                    if not placed:
                        groups.append([crop_icon])
                        group_boxes.append([box])
                
                if groups:
                    min_index = min(range(len(groups)), key=lambda i: len(groups[i]))
                    x, y, w, h = group_boxes[min_index][0]
                    return (x + w // 2, y + h // 2)
            
            height, width = img.shape[:2]
            cols, rows = 4, 2
            cell_w = width // cols
            cell_h = height // rows
            
            cells = []
            for row in range(rows):
                for col in range(cols):
                    x1 = col * cell_w
                    y1 = row * cell_h
                    x2 = (col + 1) * cell_w
                    y2 = (row + 1) * cell_h
                    
                    cell = gray[y1:y2, x1:x2]
                    if cell.size > 0:
                        cell_resized = cv2.resize(cell, (40, 40))
                        hist = cv2.calcHist([cell_resized], [0], None, [32], [0, 256])
                        cv2.normalize(hist, hist)
                        cells.append({
                            'hist': hist.flatten(),
                            'pos': (x1 + cell_w // 2, y1 + cell_h // 2)
                        })
            
            if len(cells) >= 2:
                avg_hist = np.mean([c['hist'] for c in cells], axis=0)
                diff_scores = [np.sum(np.abs(c['hist'] - avg_hist)) for c in cells]
                odd_idx = np.argmax(diff_scores)
                return cells[odd_idx]['pos']
            
            h, w = img.shape[:2]
            return (random.randint(50, w - 50), random.randint(50, h - 50))
            
        except Exception as e:
            return None

# ================= NEXTFAUCET BOT =================
class NextFaucetBot:
    def __init__(self, cookie_string, user_agent=None):
        self.s = session
        self.config_manager = ConfigManager()
        
        cookie_dict = parse_cookie(cookie_string)
        
        if not cookie_dict:
            raise ValueError("Invalid cookie format")
        
        for key, value in cookie_dict.items():
            self.s.cookies.set(key, value)
        
        self.config_manager.config["cookie_dict"] = cookie_dict
        self.config_manager.config["cookie_string"] = cookie_string
        
        if user_agent:
            self.s.headers.update({"user-agent": user_agent})
            self.config_manager.config["user_agent"] = user_agent
        else:
            default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            self.s.headers.update({"user-agent": default_ua})
            self.config_manager.config["user_agent"] = default_ua
        
        self.config_manager.save_config()
        
        # Initialize stats safely
        stats = self.config_manager.config.get("stats", {})
        self.claim_count = stats.get("total_claims", 0)
        self.total_earned = stats.get("total_earned", 0.0)
        self.level = 0
        self.balance = 0.0
    
    def get_dashboard(self, captcha_switch="iconcaptcha", retry=3):
        """Get dashboard HTML with retry"""
        for attempt in range(retry):
            try:
                url = f"{DASHBOARD}?captcha_switch={captcha_switch}"
                r = self.s.get(url, timeout=25)
                return r.text
            except requests.exceptions.Timeout:
                if attempt < retry - 1:
                    time.sleep(2)
            except Exception as e:
                if attempt < retry - 1:
                    time.sleep(2)
        return ""
    
    def login_check(self):
        """Verify login"""
        html = self.get_dashboard()
        
        if not html:
            log("Failed to load dashboard - connection issue", R)
            return False
        
        if "?logout" in html or "navBalance" in html:
            log("✓ Login successful", G)
            return True
        
        log("✗ Login failed - invalid cookie", R)
        return False
    
    def get_account_info(self):
        """Parse account info"""
        html = self.get_dashboard()
        
        if not html:
            return self.balance, self.level
        
        bal_match = re.search(r'id="navBalance">([\d,.]+)\s*</span>', html)
        if bal_match:
            try:
                self.balance = float(bal_match.group(1).replace(',', ''))
            except:
                pass
        
        level_match = re.search(r'id="lvlBadge">LVL\s*(\d+)</div>', html)
        if level_match:
            try:
                self.level = int(level_match.group(1))
            except:
                pass
        
        return self.balance, self.level
    
    def get_timer(self, html, timer_name):
        """Get timer value from HTML"""
        pattern = rf'startTimer\(\'{timer_name}\',\s*(\d+)\);'
        match = re.search(pattern, html)
        if match:
            return int(match.group(1))
        return 0
    
    def heartbeat(self, referer):
        """Send heartbeat"""
        try:
            url = DASHBOARD
            data = {"action": "heartbeat"}
            headers = {
                "referer": referer,
                "origin": BASE_URL,
                "x-requested-with": "XMLHttpRequest"
            }
            resp = self.s.post(url, data=data, headers=headers, timeout=30)
            result = resp.json()
            return result.get("ok") == 1
        except:
            return False
    
    def save_fingerprint(self, referer):
        """Save fingerprint"""
        try:
            ua = self.s.headers.get("user-agent")
            fingerprint = self.config_manager.get_fingerprint(ua)
            
            url = DASHBOARD
            data = {"action": "save_fp", "fp": fingerprint}
            headers = {
                "referer": referer,
                "origin": BASE_URL,
                "x-requested-with": "XMLHttpRequest"
            }
            resp = self.s.post(url, data=data, headers=headers, timeout=30)
            
            clicks = self.config_manager.update_clicks()
            pops = self.config_manager.update_pops()
            self.s.cookies.set("_uclicks", str(clicks))
            self.s.cookies.set("popFires", str(pops))
            
            return True
        except:
            return False
    
    def get_csrf(self, html):
        """Extract CSRF token"""
        patterns = [
            r"f\.append\('csrf_token',\s*'([^']+)'\);",
            r'name="csrf_token_name"\s+value="([^"]+)"',
            r'id="token"\s+value="([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def solve_icon_captcha(self, referer):
        """Solve IconCaptcha"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                widget_id = str(uuid.uuid4())
                current_ts = int(time.time() * 1000)
                init_ts = current_ts - random.randint(5000, 20000)
                
                load_payload = {
                    "widgetId": widget_id,
                    "action": "LOAD",
                    "theme": "light",
                    "timestamp": current_ts,
                    "initTimestamp": init_ts
                }
                
                boundary = f"----WebKitFormBoundary{random.randint(10000000, 99999999)}"
                
                load_body = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="payload"\r\n'
                    f"\r\n"
                    f"{base64.b64encode(json.dumps(load_payload).encode()).decode()}\r\n"
                    f"--{boundary}--\r\n"
                )
                
                headers = {
                    'Content-Type': f'multipart/form-data; boundary={boundary}',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': referer,
                    'Origin': BASE_URL
                }
                
                resp = self.s.post(CAPTCHA_REQUEST, data=load_body, headers=headers, timeout=30)
                response_data = IconCaptchaSolver.decode_response(resp.text)
                
                if not response_data:
                    continue
                
                challenge_id = response_data.get('identifier')
                challenge = response_data.get('challenge')
                
                if not challenge_id or not challenge:
                    continue
                
                img_b64 = IconCaptchaSolver.extract_image_from_challenge(challenge)
                
                if not img_b64:
                    continue
                
                width, height = IconCaptchaSolver.get_image_size(img_b64)
                pos = IconCaptchaSolver.solve_icon_captcha(img_b64)
                
                if not pos:
                    pos = (random.randint(0, width), random.randint(0, height))
                
                x, y = pos
                
                select_payload = {
                    "widgetId": widget_id,
                    "challengeId": challenge_id,
                    "action": "SELECTION",
                    "x": int(x),
                    "y": int(y),
                    "width": int(width),
                    "timestamp": int(time.time() * 1000),
                    "initTimestamp": init_ts
                }
                
                select_body = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="payload"\r\n'
                    f"\r\n"
                    f"{base64.b64encode(json.dumps(select_payload).encode()).decode()}\r\n"
                    f"--{boundary}--\r\n"
                )
                
                resp = self.s.post(CAPTCHA_REQUEST, data=select_body, headers=headers, timeout=30)
                result = IconCaptchaSolver.decode_response(resp.text)
                
                if result and result.get('completed') is True:
                    return widget_id, challenge_id
                
                time.sleep(1)
                
            except Exception as e:
                continue
        
        return None, None
    
    def claim_faucet(self):
        """Claim faucet reward"""
        log("┌─ FAUCET CLAIM ─", C)
        
        html = self.get_dashboard()
        
        if not html:
            log("├─ Failed to load page", R)
            return False
        
        timer = self.get_timer(html, "faucetTimer")
        
        if timer > 0:
            mins, secs = divmod(timer, 60)
            log(f"└─ Cooldown: {mins:02d}:{secs:02d}", Y)
            return None
        
        referer = f"{DASHBOARD}?captcha_switch=iconcaptcha"
        
        if not self.heartbeat(referer):
            log("├─ Heartbeat failed", R)
            return False
        log("├─ Heartbeat OK", G)
        
        if not self.save_fingerprint(referer):
            log("├─ Fingerprint failed", R)
            return False
        log("├─ Fingerprint OK", G)
        
        html = self.get_dashboard()
        csrf = self.get_csrf(html)
        
        if not csrf:
            log("├─ CSRF not found", R)
            return False
        
        # Start view
        try:
            view_data = {"action": "start_view"}
            view_headers = {
                "referer": referer,
                "origin": BASE_URL,
                "x-requested-with": "XMLHttpRequest"
            }
            view_resp = self.s.post(DASHBOARD, data=view_data, headers=view_headers, timeout=30)
            view_result = view_resp.json()
            
            if view_result.get("status") != "success":
                log("├─ Failed to start view", R)
                return False
            
            for i in range(15, 0, -1):
                temp(f"├─ Ad time left: {i:02d}s", Y)
                time.sleep(1)
            clear_line()
            log("├─ Ad completed", G)
            
            html = self.get_dashboard()
            csrf = self.get_csrf(html)
        except Exception as e:
            log(f"├─ View error: {e}", R)
            return False
        
        log("├─ Solving captcha...", Y)
        wid, cid = self.solve_icon_captcha(referer)
        
        if not wid:
            log("├─ Captcha failed", R)
            return False
        log("├─ Captcha solved", G)
        
        try:
            files = {
                "action": (None, "claim_direct"),
                "csrf_token": (None, csrf),
                "ic-rq": (None, "1"),
                "ic-wid": (None, wid),
                "ic-cid": (None, cid),
                "ic-hp": (None, ""),
                "adblock": (None, "0")
            }
            
            resp = self.s.post(DASHBOARD, files=files, timeout=30)
            result = resp.json()
            
            if result.get("status") == "success":
                reward = float(result.get("final_reward", 0))
                self.claim_count += 1
                self.total_earned += reward
                self.balance += reward
                self.config_manager.update_stats(reward, True)
                
                log(f"├─ Reward: {reward:.8f} BCH", G)
                log(f"└─ Balance: {self.balance:.8f} BCH", C)
                return True
            else:
                msg = result.get("msg", result.get("error", "Unknown"))
                log(f"└─ Failed: {msg}", R)
                self.config_manager.update_stats(0, False)
                return False
                
        except Exception as e:
            log(f"└─ Error: {e}", R)
            self.config_manager.update_stats(0, False)
            return False
    
    def claim_scratch(self):
        """Claim scratch card"""
        log("┌─ SCRATCH CARD ─", M)
        
        html = self.get_dashboard()
        
        if not html:
            log("├─ Failed to load page", R)
            return False
        
        timer = self.get_timer(html, "scratchTimer")
        
        if timer > 0:
            mins, secs = divmod(timer, 60)
            log(f"└─ Cooldown: {mins:02d}:{secs:02d}", Y)
            return None
        
        referer = f"{DASHBOARD}?captcha_switch=iconcaptcha"
        
        if not self.heartbeat(referer):
            log("├─ Heartbeat failed", R)
            return False
        log("├─ Heartbeat OK", G)
        
        if not self.save_fingerprint(referer):
            log("├─ Fingerprint failed", R)
            return False
        log("├─ Fingerprint OK", G)
        
        html = self.get_dashboard()
        csrf = self.get_csrf(html)
        
        if not csrf:
            log("├─ CSRF not found", R)
            return False
        
        log("├─ Solving captcha...", Y)
        wid, cid = self.solve_icon_captcha(referer)
        
        if not wid:
            log("├─ Captcha failed", R)
            return False
        log("├─ Captcha solved", G)
        
        try:
            files = {
                "action": (None, "claim_scratch"),
                "csrf_token": (None, csrf),
                "ic-rq": (None, "1"),
                "ic-wid": (None, wid),
                "ic-cid": (None, cid),
                "ic-hp": (None, ""),
                "adblock": (None, "0")
            }
            
            resp = self.s.post(DASHBOARD, files=files, timeout=30)
            result = resp.json()
            
            if result.get("status") == "success":
                reward = float(result.get("final_reward", 0))
                self.claim_count += 1
                self.total_earned += reward
                self.balance += reward
                self.config_manager.update_stats(reward, True)
                
                log(f"├─ Reward: {reward:.8f} BCH", G)
                log(f"└─ Balance: {self.balance:.8f} BCH", C)
                return True
            else:
                msg = result.get("msg", result.get("error", "Unknown"))
                log(f"└─ Failed: {msg}", R)
                self.config_manager.update_stats(0, False)
                return False
                
        except Exception as e:
            log(f"└─ Error: {e}", R)
            self.config_manager.update_stats(0, False)
            return False
    
    def claim_slots(self):
        """Claim slot spin"""
        log("┌─ SLOT SPIN ─", Y)
        
        html = self.get_dashboard()
        
        if not html:
            log("├─ Failed to load page", R)
            return False
        
        timer = self.get_timer(html, "slotTimer")
        
        if timer > 0:
            mins, secs = divmod(timer, 60)
            log(f"└─ Cooldown: {mins:02d}:{secs:02d}", Y)
            return None
        
        referer = f"{DASHBOARD}?captcha_switch=iconcaptcha"
        
        if not self.heartbeat(referer):
            log("├─ Heartbeat failed", R)
            return False
        log("├─ Heartbeat OK", G)
        
        if not self.save_fingerprint(referer):
            log("├─ Fingerprint failed", R)
            return False
        log("├─ Fingerprint OK", G)
        
        log("├─ Solving captcha...", Y)
        wid, cid = self.solve_icon_captcha(referer)
        
        if not wid:
            log("├─ Captcha failed", R)
            return False
        log("├─ Captcha solved", G)
        
        try:
            files = {
                "action": (None, "slot_spin"),
                "ic-rq": (None, "1"),
                "ic-wid": (None, wid),
                "ic-cid": (None, cid),
                "ic-hp": (None, "")
            }
            
            resp = self.s.post(DASHBOARD, files=files, timeout=30)
            result = resp.json()
            
            if result.get("status") == "success":
                reward = float(result.get("bch_won", 0))
                self.claim_count += 1
                self.total_earned += reward
                self.balance += reward
                self.config_manager.update_stats(reward, True)
                
                log(f"├─ Reward: {reward:.8f} BCH", G)
                log(f"└─ Balance: {self.balance:.8f} BCH", C)
                return True
            else:
                msg = result.get("msg", result.get("error", "Unknown"))
                log(f"└─ Failed: {msg}", R)
                self.config_manager.update_stats(0, False)
                return False
                
        except Exception as e:
            log(f"└─ Error: {e}", R)
            self.config_manager.update_stats(0, False)
            return False

# ================= MAIN =================
def print_dashboard(bot):
    print_separator()
    print(f"  {G}►{W} Script      : {C}NextFaucet Bot v6.0{W}")
    print(f"  {G}►{W} Balance    : {Y}{bot.balance:.8f} BCH{W}")
    print(f"  {G}►{W} Level      : {Y}{bot.level}{W}")
    print(f"  {G}►{W} Claims     : {Y}{bot.claim_count}{W}")
    print(f"  {G}►{W} Total Earned: {Y}{bot.total_earned:.8f} BCH{W}")
    print_separator()

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

def main():
    clear()
    banner()

    # Cookie load karo - env > cookies.txt > input
    cookie = os.environ.get("COOKIE_STRING", "").strip()

    if not cookie and os.path.exists("cookies.txt"):
        with open("cookies.txt") as f:
            cookie = f.read().strip()
        log("Cookie loaded from cookies.txt", G)

    if not cookie:
        print(f"{D}┌────────────────────────────────────────────────────────┐{W}")
        print(f"{D}│ Paste your cookie string directly                      │{W}")
        print(f"{D}│ Example: PHPSESSID=xxx; _uclicks=xxx; popFires=xxx    │{W}")
        print(f"{D}└────────────────────────────────────────────────────────┘{W}")
        cookie = input(f"{B}{C}│ Cookie : {W}").strip()

    user_agent = os.environ.get("USER_AGENT", "").strip()
    if not user_agent:
        user_agent = ""

    if not cookie:
        log("Cookie is required!", R)
        sys.exit(1)
    
    try:
        bot = NextFaucetBot(cookie, user_agent if user_agent else None)
    except ValueError as e:
        log(f"Error: {e}", R)
        sys.exit(1)
    
    if not bot.login_check():
        log("Login failed! Check your cookie format.", R)
        sys.exit(1)
    
    bot.get_account_info()
    log("Bot started!", G)
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

if __name__ == "__main__":
    main()
