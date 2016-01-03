# -*- coding: utf-8 -*-
# flake8: noqa
"""
Python PKCS#5 v2.0 PBKDF2 Module
--------------------------------

This module implements the password-based key derivation function, PBKDF2,
specified in `RSA PKCS#5 v2.0 <http://www.rsa.com/rsalabs/node.asp?id=2127>`_.

Example PBKDF2 usage
====================

::

 from pbkdf2 import PBKDF2
 from Crypto.Cipher import AES
 import os

 salt = os.urandom(8)    # 64-bit salt
 key = PBKDF2("This passphrase is a secret.", salt).read(32) # 256-bit key
 iv = os.urandom(16)     # 128-bit IV
 cipher = AES.new(key, AES.MODE_CBC, iv)
 # ...

Example crypt() usage
=====================

::

 from pbkdf2 import crypt
 pwhash = crypt("secret")
 alleged_pw = raw_input("Enter password: ")
 if pwhash == crypt(alleged_pw, pwhash):
     print "Password good"
 else:
     print "Invalid password"

Example crypt() output
======================

::

 >>> from pbkdf2 import crypt
 >>> crypt("secret")
 '$p5k2$$hi46RA73$aGBpfPOgOrgZLaHGweSQzJ5FLz4BsQVs'
 >>> crypt("secret", "XXXXXXXX")
 '$p5k2$$XXXXXXXX$L9mVVdq7upotdvtGvXTDTez3FIu3z0uG'
 >>> crypt("secret", "XXXXXXXX", 400)  # 400 iterations (the default for crypt)
 '$p5k2$$XXXXXXXX$L9mVVdq7upotdvtGvXTDTez3FIu3z0uG'
 >>> crypt("spam", iterations=400)
 '$p5k2$$FRsH3HJB$SgRWDNmB2LukCy0OTal6LYLHZVgtOi7s'
 >>> crypt("spam", iterations=1000)    # 1000 iterations
 '$p5k2$3e8$H0NX9mT/$wk/sE8vv6OMKuMaqazCJYDSUhWY9YB2J'


Resources
=========

Homepage
    https://www.dlitz.net/software/python-pbkdf2/

Source Code
    https://github.com/dlitz/python-pbkdf2/

PyPI package name
    `pbkdf2 <http://pypi.python.org/pypi/pbkdf2>`_

License
=======
Copyright (C) 2007-2011 Dwayne C. Litzenberger <dlitz@dlitz.net>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import hmac
import hashlib
from base64 import b64encode, b64decode
from itertools import izip, starmap
from operator import xor
from os import urandom
from struct import Struct


def pbkdf2_bin(data, salt, iterations=1000, keylen=24, hashfunc=None):
    """Returns a binary digest for the PBKDF2 hash algorithm of `data`
    with the given `salt`.  It iterates `iterations` time and produces a
    key of `keylen` bytes.  By default SHA-1 is used as hash function,
    a different hashlib `hashfunc` can be provided.
    """
    _pack_int = Struct(">I").pack
    hashfunc = hashfunc or hashlib.sha1
    mac = hmac.new(data, None, hashfunc)

    def _pseudorandom(x, mac=mac):
        h = mac.copy()
        h.update(x)
        return map(ord, h.digest())

    buf = []
    for block in xrange(1, -(-keylen // mac.digest_size) + 1):
        rv = u = _pseudorandom(salt + _pack_int(block))
        for _ in xrange(iterations - 1):
            u = _pseudorandom("".join(map(chr, u)))
            rv = starmap(xor, izip(rv, u))
        buf.extend(rv)
    return "".join(map(chr, buf))[:keylen]

# Parameters to PBKDF2. Only affect new passwords.
SALT_LENGTH = 12
KEY_LENGTH = 24
HASH_FUNCTION = "sha256"  # Must be in hashlib.
# Linear to the hashing time. Adjust to be high but take a reasonable
# amount of time on your server. Measure with:
# python -m timeit -s "import passwords as p" "p.make_hash("something")"
COST_FACTOR = 1000


def pbkdf2(password):
    """Generate a random salt and return a new hash for the password."""
    if isinstance(password, unicode):
        password = password.encode("utf-8")
    salt = b64encode(urandom(SALT_LENGTH))
    return "PBKDF2${}${}${}${}".format(
        HASH_FUNCTION,
        COST_FACTOR,
        salt,
        b64encode(pbkdf2_bin(password, salt, COST_FACTOR, KEY_LENGTH,
                             getattr(hashlib, HASH_FUNCTION))))


def pbkdf2_check(raw_password, encrypted_passwd):
    """Check a password against an existing hash."""
    if isinstance(raw_password, unicode):
        raw_password = raw_password.encode("utf-8")
    algorithm, hash_function, cost_factor, salt, derived_key = encrypted_passwd.split("$")
    assert algorithm == "PBKDF2"
    derived_key = b64decode(derived_key)
    hash_b = pbkdf2_bin(raw_password, salt, int(cost_factor), len(derived_key),
                        getattr(hashlib, hash_function))
    assert len(derived_key) == len(hash_b)  # we requested thisfrom helper.pbkdf2_bin()
    # Same as "return hash_a == hash_b" but takes a constant time.
    # See http://carlos.bueno.org/2011/10/timing.html
    diff = 0
    for char_a, char_b in izip(derived_key, hash_b):
        diff |= ord(char_a) ^ ord(char_b)
    return diff == 0
