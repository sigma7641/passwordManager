import hashlib
import json
import os
import uuid

from src.core.encryption import decrypt_aes, encrypt_aes
from src.utils.logger import debug


class PasswordManager:
    def __init__(self, master_password):
        self._master_password = hashlib.sha256(master_password.encode()).digest()
        if os.path.exists("passwords.json.aes"):
            with open("passwords.json.aes", "rb") as f:
                encrypted_data = f.read()

            try:
                decrypted_data = decrypt_aes(encrypted_data, self._master_password)
                self.passwords = json.loads(decrypted_data)
            except ValueError as e:
                raise ValueError(f"Invalid Master Password! {e}")
        else:
            self.passwords = {}

    @debug
    def save_passwords(self):
        data = json.dumps(self.passwords).encode()
        encrypted_data = encrypt_aes(data, self._master_password)
        with open("passwords.json.aes", "wb") as f:
            f.write(encrypted_data)

    @debug
    def add_password(self, password_info_dict):
        unique_id = str(uuid.uuid4())
        self.passwords[unique_id] = {
            "title": "",
            "password": "",
            "note": "",
        }
        self.passwords[unique_id].update(password_info_dict)
        self.save_passwords()

    @debug
    def delete_password(self, uid):
        del self.passwords[uid]
        self.save_passwords()

    @debug
    def get_password_info(self, index):
        password_info = self.passwords[index]
        return password_info

    @debug
    def update_password(self, index, password_info_dict) -> bool:
        try:
            self.passwords[index].update(password_info_dict)
        except KeyError:
            raise KeyError(f"Password with index {index} not found.")
        self.save_passwords()
        return True
