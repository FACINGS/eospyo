"""Utility functions."""


import hashlib
import hmac
import io
import struct

import base58
import cryptos


def sign_bytes(*, bytes_: bytes, key: str) -> str:
    _check_bytes(bytes_)

    nonce = 0
    sha256 = hashlib.sha256()
    sha256.update(bytes_)
    while True:
        v, r, s = _ecdsa_raw_sign_nonce(sha256.digest(), key, nonce)
        signature = v.to_bytes(1, "big")
        signature += r.to_bytes(32, "big") + s.to_bytes(32, "big")
        if _is_canonical(signature):
            signature = b"\x00" + signature
            break
        nonce += 1

    ds = io.BytesIO(signature)
    first_byte = ds.read(1)
    t = struct.unpack("<B", first_byte)[0]
    if t == 0:
        data = ds.read(65)
        data = data + _ripmed160(data + b"K1")[:4]
        signature = "SIG_K1_" + base58.b58encode(data).decode("ascii")
    elif t == 1:
        raise NotImplementedError("Not Implemented")
    else:
        raise ValueError("Invalid binary signature")

    return signature


def _check_bytes(bytes_):
    if len(bytes_) == 0:
        raise ValueError("Can not sign empty bytes")
    if not isinstance(bytes_, bytes):
        msg = f"sign_bytes requires 'byte' type. But '{type(bytes_)}' received"
        raise TypeError(msg)


def _ripmed160(data):
    try:
        h = hashlib.new("ripemd160")
    except ValueError:
        from Crypto.Hash import RIPEMD160  # NOQA: I001

        h = RIPEMD160.new()
    h.update(data)
    return h.digest()


def _is_canonical(signature):
    canonical = all(
        [
            not (signature[1] & 0x80),
            not (signature[1] == 0 and not (signature[2] & 0x80)),
            not (signature[33] & 0x80),
            not (signature[33] == 0 and not (signature[34] & 0x80)),
        ]
    )
    return canonical


def _ecdsa_raw_sign_nonce(message_hash, key, nonce):
    msg_int = cryptos.hash_to_int(message_hash)
    k = _deterministic_generate_k_nonce(message_hash, key, nonce)

    r, y = cryptos.fast_multiply(cryptos.G, k)
    s = (
        cryptos.inv(k, cryptos.N)
        * (msg_int + r * cryptos.decode_privkey(key))  # NOQA: W503
        % cryptos.N
    )

    v = 27 + ((y % 2) ^ (0 if s * 2 < cryptos.N else 1))
    s = s if s * 2 < cryptos.N else cryptos.N - s

    if "compressed" in cryptos.get_privkey_format(key):
        v += 4

    return v, r, s


def _deterministic_generate_k_nonce(message_hash, key, nonce):
    v = b"\x01" * 32
    k = b"\x00" * 32
    try:
        key_encoded = cryptos.encode_privkey(key, "bin")
    except AssertionError:
        raise ValueError("Error in private key provided: {key=}")

    msg_int = cryptos.hash_to_int(message_hash)
    message_hash = cryptos.encode(msg_int + nonce, 256, 32)

    k = _sha256_hmac_digest(k, v + b"\x00" + key_encoded + message_hash)
    v = _sha256_hmac_digest(k, v)
    k = _sha256_hmac_digest(k, v + b"\x01" + key_encoded + message_hash)
    v = _sha256_hmac_digest(k, v)
    k = _sha256_hmac_digest(k, v)

    k = cryptos.decode(k, 256)
    return k


def _sha256_hmac_digest(key, msg):
    value = hmac.new(key, msg, digestmod=hashlib.sha256)
    digest = value.digest()
    return digest
