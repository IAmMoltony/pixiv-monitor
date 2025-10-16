import requests
import os
import threading
import time

USER_AGENT = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"

class ApiToken:
    def __init__(self, access, refresh):
        self.access_token = access
        self.refresh_token = refresh

    def refresh(self):
        response = requests.post(
            AUTH_TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "include_policy": "true",
                "refresh_token": self.refresh_token,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=30
        )
        
        data = response.json()
        self.refresh_token = data["refresh_token"] # pretty sure its constant
        self.access_token = data["access_token"]

class TokenSwitcher:
    def __init__(self, num_accounts, load_tokens=True):
        self.num_accounts = num_accounts
        self.tokens = []
        if load_tokens:
            for i in range(self.num_accounts):
                self.tokens.append(ApiToken(os.getenv(f"ACCESS_TOKEN{i}"), os.getenv(f"REFRESH_TOKEN{i}")))
        self.current_token = 0
        self.lock = threading.Lock()
        self.last_switch_time = 0
        self.cooldown = 3

    def get_access_token(self):
        return self.tokens[self.current_token].access_token

    def switch_token(self):
        with self.lock:
            now = time.monotonic()
            if now - self.last_switch_time < self.cooldown:
                return
            self.current_token += 1
            if self.current_token >= self.num_accounts:
                self.current_token = 0
            self.last_switch_time = now

    def refresh_token(self):
        self.tokens[self.current_token].refresh()
