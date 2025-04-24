import hashlib
import time
from dataclasses import dataclass
from typing import Optional

import pyotp


@dataclass
class OTPInfo:
    name: str
    otp: str
    remaining_seconds: int


class OTPGenerator:
    def __init__(
        self,
        name: str,
        secret: str,
        digits: int = 6,
        algorithm: str = "SHA1",
        interval: int = 30,
    ):
        self.name = name
        self.secret = secret
        self.digits = digits
        self.digest = getattr(hashlib, algorithm.lower(), hashlib.sha1)
        self.interval = interval
        self._totp = pyotp.TOTP(
            s=secret, digits=digits, digest=self.digest, interval=interval
        )

    def generate(self) -> OTPInfo:
        """OTPコードと残り時間を生成します"""
        current_time = time.time()
        time_remaining = self.interval - (int(current_time) % self.interval)

        return OTPInfo(
            name=self.name, otp=self._totp.now(), remaining_seconds=time_remaining
        )

    @staticmethod
    def from_winauth_data(name: str, secret_data: str) -> Optional["OTPGenerator"]:
        """WinAuthのsecret_dataからOTPGeneratorを生成します"""
        try:
            parts = secret_data.strip().split()
            if len(parts) >= 4:
                secret = parts[0]
                digits = int(parts[1])
                algo = parts[2].upper()
                interval = int(parts[3])
            else:
                secret = parts[0]
                digits = 6
                algo = "SHA1"
                interval = 30

            return OTPGenerator(
                name=name,
                secret=secret,
                digits=digits,
                algorithm=algo,
                interval=interval,
            )
        except Exception:
            return None
