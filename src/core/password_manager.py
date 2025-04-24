import hashlib
import json
import os
import threading
import uuid
import xml.etree.ElementTree as ET
from threading import Event
from typing import Optional

import yaml

from src.core.encryption import decrypt_aes, encrypt_aes
from src.core.otp_generator import OTPGenerator
from src.utils.logger import debug


class PasswordManager:
    def __init__(self, master_password):
        self._master_password = hashlib.sha256(master_password.encode()).digest()
        self.passwords = {}
        self._is_loaded = False
        self._load_lock = threading.Lock()
        self._load_event = Event()
        self._config = self._load_or_create_config()
        self._winauth_data = {}

    def _load_or_create_config(self):
        """設定ファイルを読み込むか、存在しない場合は作成します"""
        if not os.path.exists("config.yaml"):
            config = {
                "password_file": "passwords.json.aes",
                "winauth_file": "winauth.xml",
            }
            with open("config.yaml", "w") as f:
                yaml.dump(config, f)
            return config

        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)

    def _load_winauth_xml(self):
        """WinAuthのXMLファイルを読み込みます"""
        if not os.path.exists(self._config["winauth_file"]):
            return

        tree = ET.parse(self._config["winauth_file"])
        root = tree.getroot()

        for auth in root.findall("WinAuthAuthenticator"):
            name = auth.findtext("name")
            if not name:
                continue

            auth_data = auth.find("authenticatordata")
            if auth_data is None:
                continue

            secretdata = auth_data.findtext("secretdata")
            if secretdata:
                self._winauth_data[name] = secretdata

    def _load_passwords_async(self, callback=None):
        def worker():
            try:
                with self._load_lock:
                    if os.path.exists(self._config["password_file"]):
                        with open(self._config["password_file"], "rb") as f:
                            encrypted_data = f.read()

                        try:
                            decrypted_data = decrypt_aes(
                                encrypted_data, self._master_password
                            )
                            self.passwords = json.loads(decrypted_data)
                            self._is_loaded = True
                            # WinAuthのデータを読み込み
                            self._load_winauth_xml()
                            if callback:
                                callback(True, None)
                        except ValueError as e:
                            if callback:
                                callback(False, f"Invalid Master Password! {e}")
                    else:
                        self.passwords = {}
                        self._is_loaded = True
                        if callback:
                            callback(True, None)
                    self._load_event.set()
            except Exception as e:
                if callback:
                    callback(False, str(e))
                self._load_event.set()

        threading.Thread(target=worker).start()

    def load_passwords(self, callback=None):
        """パスワードファイルを非同期で読み込みます"""
        self._load_passwords_async(callback)

    def load_passwords_sync(self):
        """パスワードファイルを同期的に読み込みます（読み込み完了まで待機）"""
        self._load_event.clear()
        self._load_passwords_async()
        self._load_event.wait()  # 読み込み完了まで待機
        if not self._is_loaded:
            raise RuntimeError("Failed to load passwords")
        return self.passwords

    def _ensure_loaded(self):
        """パスワードが読み込まれているか確認します"""
        if not self._is_loaded:
            raise RuntimeError(
                "Passwords are not loaded yet. Call load_passwords() first."
            )

    def _save_passwords_async(self, callback=None):
        def worker():
            try:
                self._ensure_loaded()
                data = json.dumps(self.passwords).encode()
                encrypted_data = encrypt_aes(data, self._master_password)
                with open(self._config["password_file"], "wb") as f:
                    f.write(encrypted_data)
                if callback:
                    callback(True, None)
            except Exception as e:
                if callback:
                    callback(False, str(e))

        threading.Thread(target=worker).start()

    @debug
    def save_passwords(self, callback=None):
        self._save_passwords_async(callback)

    @debug
    def add_password(self, password_info_dict, callback=None):
        self._ensure_loaded()
        unique_id = str(uuid.uuid4())
        self.passwords[unique_id] = {
            "title": "",
            "password": "",
            "note": "",
        }
        self.passwords[unique_id].update(password_info_dict)
        self._save_passwords_async(callback)

    @debug
    def delete_password(self, uid, callback=None):
        self._ensure_loaded()
        del self.passwords[uid]
        self._save_passwords_async(callback)

    @debug
    def get_password_info(self, index):
        self._ensure_loaded()
        password_info = self.passwords[index]
        return password_info

    @debug
    def update_password(self, index, password_info_dict, callback=None):
        self._ensure_loaded()
        try:
            self.passwords[index].update(password_info_dict)
        except KeyError:
            raise KeyError(f"Password with index {index} not found.")
        self._save_passwords_async(callback)
        return True

    @debug
    def get_otp(self, password_id: str) -> Optional[OTPGenerator]:
        """パスワードに紐づくOTP生成器を取得します"""
        self._ensure_loaded()
        try:
            password_info = self.passwords[password_id]
            winauth_name = password_info.get("winauth_name")
            if not winauth_name or winauth_name not in self._winauth_data:
                return None

            return OTPGenerator.from_winauth_data(
                name=winauth_name, secret_data=self._winauth_data[winauth_name]
            )
        except Exception:
            return None
