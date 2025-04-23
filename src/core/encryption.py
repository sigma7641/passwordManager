from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt_aes(data, key):
    """AES暗号化を行う関数"""
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes


def decrypt_aes(ciphertext, key):
    """AES復号を行う関数"""
    iv = ciphertext[:16]
    ct = ciphertext[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return unpad(cipher.decrypt(ct), AES.block_size)
