import hashlib
import json
import os
import threading
import uuid
from threading import Event

from src.core.encryption import decrypt_aes, encrypt_aes
from src.utils.logger import debug


class PasswordManager:
    def __init__(self, master_password):
        self._master_password = hashlib.sha256(master_password.encode()).digest()
        self.passwords = {}
        self._is_loaded = False
        self._load_lock = threading.Lock()
        self._load_event = Event()

    def _load_passwords_async(self, callback=None):
        def worker():
            try:
                with self._load_lock:
                    if os.path.exists("passwords.json.aes"):
                        with open("passwords.json.aes", "rb") as f:
                            encrypted_data = f.read()

                        try:
                            decrypted_data = decrypt_aes(
                                encrypted_data, self._master_password
                            )
                            self.passwords = json.loads(decrypted_data)
                            self._is_loaded = True
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
                with open("passwords.json.aes", "wb") as f:
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
