# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

import pytest

from rhodecode.lib.encrypt import (
    AESCipher, SignatureVerificationError, InvalidDecryptedValue)
from rhodecode.lib.encrypt2 import (Encryptor, InvalidToken)


class TestEncryptModule(object):

    @pytest.mark.parametrize(
        "key, text",
        [
            ('a', 'short'),
            ('a'*64, 'too long(trimmed to 32)'),
            ('a'*32, 'just enough'),
            ('ąćęćę', 'non asci'),
            ('$asa$asa', 'special $ used'),
        ]
    )
    def test_encryption(self, key, text):
        enc = AESCipher(key).encrypt(text)
        assert AESCipher(key).decrypt(enc) == text

    def test_encryption_with_hmac(self):
        key = 'secret'
        text = 'ihatemysql'
        enc = AESCipher(key, hmac=True).encrypt(text)
        assert AESCipher(key, hmac=True).decrypt(enc) == text

    def test_encryption_with_hmac_with_bad_key(self):
        key = 'secretstring'
        text = 'ihatemysql'
        enc = AESCipher(key, hmac=True).encrypt(text)

        with pytest.raises(SignatureVerificationError) as e:
            assert AESCipher('differentsecret', hmac=True).decrypt(enc) == ''

        assert 'Encryption signature verification failed' in str(e)

    def test_encryption_with_hmac_with_bad_data(self):
        key = 'secret'
        text = 'ihatemysql'
        enc = AESCipher(key, hmac=True).encrypt(text)
        enc = 'xyz' + enc[3:]
        with pytest.raises(SignatureVerificationError) as e:
            assert AESCipher(key, hmac=True).decrypt(enc) == text

        assert 'Encryption signature verification failed' in str(e)

    def test_encryption_with_hmac_with_bad_key_not_strict(self):
        key = 'secretstring'
        text = 'ihatemysql'
        enc = AESCipher(key, hmac=True).encrypt(text)

        assert isinstance(AESCipher(
            'differentsecret', hmac=True, strict_verification=False
        ).decrypt(enc), InvalidDecryptedValue)


class TestEncryptModule2(object):

    @pytest.mark.parametrize(
        "key, text",
        [
            ('a', 'short'),
            ('a'*64, 'too long(trimmed to 32)'),
            ('a'*32, 'just enough'),
            ('ąćęćę', 'non asci'),
            ('$asa$asa', 'special $ used'),
        ]
    )
    def test_encryption(self, key, text):
        enc = Encryptor(key).encrypt(text)
        assert Encryptor(key).decrypt(enc) == text

    def test_encryption_with_bad_key(self):
        key = 'secretstring'
        text = 'ihatemysql'
        enc = Encryptor(key).encrypt(text)

        assert Encryptor('differentsecret').decrypt(enc) == ''

    def test_encryption_with_bad_key_raises(self):
        key = 'secretstring'
        text = 'ihatemysql'
        enc = Encryptor(key).encrypt(text)

        with pytest.raises(InvalidToken) as e:
            Encryptor('differentsecret').decrypt(enc, safe=False)

        assert 'InvalidToken' in str(e)

    def test_encryption_with_bad_format_data(self):
        key = 'secret'
        text = 'ihatemysql'
        enc = Encryptor(key).encrypt(text)
        enc = '$xyz' + enc[3:]

        with pytest.raises(ValueError) as e:
            Encryptor(key).decrypt(enc, safe=False)

        assert 'Encrypted Data has invalid format' in str(e)

    def test_encryption_with_bad_data(self):
        key = 'secret'
        text = 'ihatemysql'
        enc = Encryptor(key).encrypt(text)
        enc = enc[:-5]

        with pytest.raises(InvalidToken) as e:
            Encryptor(key).decrypt(enc, safe=False)

        assert 'InvalidToken' in str(e)
