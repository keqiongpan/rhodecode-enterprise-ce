import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryptor(object):
    key_format = 'enc2$salt:{}$data:{}'
    pref_len = 5  # salt:, data:

    def __init__(self, enc_key):
        self.enc_key = enc_key

    def b64_encode(self, data):
        return base64.urlsafe_b64encode(data)

    def b64_decode(self, data):
        return base64.urlsafe_b64decode(data)

    def get_encryptor(self, salt):
        """
        Uses Fernet as encryptor with HMAC signature
        :param salt: random salt used for encrypting the data
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = self.b64_encode(kdf.derive(self.enc_key))
        return Fernet(key)

    def _get_parts(self, enc_data):
        parts = enc_data.split('$', 3)
        if len(parts) != 3:
            raise ValueError('Encrypted Data has invalid format, expected {}'.format(self.key_format))
        prefix, salt, enc_data = parts

        try:
            salt = self.b64_decode(salt[self.pref_len:])
        except TypeError:
            # bad base64
            raise ValueError('Encrypted Data salt invalid format, expected base64 format')

        enc_data = enc_data[self.pref_len:]
        return prefix, salt, enc_data

    def encrypt(self, data):
        salt = os.urandom(64)
        encryptor = self.get_encryptor(salt)
        enc_data = encryptor.encrypt(data)
        return self.key_format.format(self.b64_encode(salt), enc_data)

    def decrypt(self, data, safe=True):
        parts = self._get_parts(data)
        salt = parts[1]
        enc_data = parts[2]
        encryptor = self.get_encryptor(salt)
        try:
            return encryptor.decrypt(enc_data)
        except (InvalidToken,):
            if safe:
                return ''
            else:
                raise
