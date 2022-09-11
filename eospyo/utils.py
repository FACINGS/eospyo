"""Utility functions."""

import hashlib
import hmac
import io
import re
import struct

import base58

A = 0
P = 2**256 - 2**32 - 977
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337  # NOQA: E501
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240  # NOQA: E501
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424  # NOQA: E501
G = (Gx, Gy)


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
    msg_int = hash_to_int(message_hash)
    k = _deterministic_generate_k_nonce(message_hash, key, nonce)

    r, y = fast_multiply(G, k)
    s = inv(k, N) * (msg_int + r * decode_privkey(key)) % N  # NOQA: W503

    v = 27 + ((y % 2) ^ (0 if s * 2 < N else 1))
    s = s if s * 2 < N else N - s

    if "compressed" in get_privkey_format(key):
        v += 4

    return v, r, s


def _deterministic_generate_k_nonce(message_hash, key, nonce):
    v = b"\x01" * 32
    k = b"\x00" * 32
    try:
        key_encoded = encode_privkey(key, "bin")
    except AssertionError:
        raise ValueError("Error in private key provided: {key=}")

    msg_int = hash_to_int(message_hash)
    message_hash = _encode(msg_int + nonce, 256, 32)

    k = _sha256_hmac_digest(k, v + b"\x00" + key_encoded + message_hash)
    v = _sha256_hmac_digest(k, v)
    k = _sha256_hmac_digest(k, v + b"\x01" + key_encoded + message_hash)
    v = _sha256_hmac_digest(k, v)
    k = _sha256_hmac_digest(k, v)

    k = _decode(k, 256)
    return k


def _sha256_hmac_digest(key, msg):
    value = hmac.new(key, msg, digestmod=hashlib.sha256)
    digest = value.digest()
    return digest


CODE_STRINGS = {
    2: "01",
    10: "0123456789",
    16: "0123456789abcdef",
    32: "abcdefghijklmnopqrstuvwxyz234567",
    58: "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
    256: "".join([chr(x) for x in range(256)]),
}


def _encode(val, base, minlen=0):
    base, minlen = int(base), int(minlen)
    code_string = CODE_STRINGS[base]
    result_bytes = bytes()
    while val > 0:
        curcode = code_string[val % base]
        result_bytes = bytes([ord(curcode)]) + result_bytes
        val //= base

    pad_size = minlen - len(result_bytes)

    if base == 256:
        padding_element = b"\x00"
    elif base == 58:
        padding_element = b"1"
    else:
        padding_element = b"0"

    if pad_size > 0:
        result_bytes = padding_element * pad_size + result_bytes

    result_string = "".join([chr(y) for y in result_bytes])
    result = result_bytes if base == 256 else result_string

    return result


def _decode(string, base):  # NOQA: C901
    if base == 256 and isinstance(string, str):
        string = bytes(bytearray.fromhex(string))
    base = int(base)
    code_string = CODE_STRINGS[base]
    result = 0
    if base == 256:

        def extract(d, cs):
            return d

    else:

        def extract(d, cs):
            return cs.find(d if isinstance(d, str) else chr(d))

    if base == 16:
        string = string.lower()
    while len(string) > 0:
        result *= base
        result += extract(string[0], code_string)
        string = string[1:]
    return result


def lpad(msg, symbol, length):
    if len(msg) >= length:
        return msg
    return symbol * (length - len(msg)) + msg


def changebase(string, frm, to, minlen=0):
    if frm == to:
        return lpad(string, CODE_STRINGS[frm][0], minlen)
    return _encode(_decode(string, frm), to, minlen)


def bin_dbl_sha256(s):
    bytes_to_hash = from_string_to_bytes(s)
    return hashlib.sha256(hashlib.sha256(bytes_to_hash).digest()).digest()


def from_string_to_bytes(a):
    return a if isinstance(a, bytes) else bytes(a, "utf-8")


def b58check_to_bin(inp):
    leadingzbytes = len(re.match("^1*", inp).group(0))
    data = b"\x00" * leadingzbytes + changebase(inp, 58, 256)
    assert bin_dbl_sha256(data[:-4])[:4] == data[-4:]
    return data[1:-4]


def get_privkey_format(priv):  # NOQA: C901
    if isinstance(priv, (int, float)):
        return "decimal"
    elif len(priv) == 32:
        return "bin"
    elif len(priv) == 33:
        return "bin_compressed"
    elif len(priv) == 64:
        return "hex"
    elif len(priv) == 66:
        return "hex_compressed"
    else:
        bin_p = b58check_to_bin(priv)
        if len(bin_p) == 32:
            return "wif"
        elif len(bin_p) == 33:
            return "wif_compressed"
        else:
            raise Exception("WIF does not represent privkey")


def from_int_to_byte(a):
    return bytes([a])


def bin_to_b58check(inp, magicbyte=0):
    if magicbyte == 0:
        inp = from_int_to_byte(0) + inp
    while magicbyte > 0:
        inp = from_int_to_byte(magicbyte % 256) + inp
        magicbyte //= 256

    leadingzbytes = 0
    for x in inp:
        if x != 0:
            break
        leadingzbytes += 1

    checksum = bin_dbl_sha256(inp)[:4]
    return "1" * leadingzbytes + changebase(inp + checksum, 256, 58)


def encode_privkey(priv, formt, vbyte=0):  # NOQA: C901
    if not isinstance(priv, (int, float)):
        return encode_privkey(decode_privkey(priv), formt, vbyte)
    if formt == "decimal":
        return priv
    elif formt == "bin":
        return _encode(priv, 256, 32)
    elif formt == "bin_compressed":
        return _encode(priv, 256, 32) + b"\x01"
    elif formt == "hex":
        return _encode(priv, 16, 64)
    elif formt == "hex_compressed":
        return _encode(priv, 16, 64) + "01"
    elif formt == "wif":
        return bin_to_b58check(_encode(priv, 256, 32), 128 + int(vbyte))
    elif formt == "wif_compressed":
        return bin_to_b58check(
            _encode(priv, 256, 32) + b"\x01", 128 + int(vbyte)
        )
    else:
        raise Exception("Invalid format!")


def decode_privkey(priv, formt=None):  # NOQA: C901
    if not formt:
        formt = get_privkey_format(priv)
    if formt == "decimal":
        return priv
    elif formt == "bin":
        return _decode(priv, 256)
    elif formt == "bin_compressed":
        return _decode(priv[:32], 256)
    elif formt == "hex":
        return _decode(priv, 16)
    elif formt == "hex_compressed":
        return _decode(priv[:64], 16)
    elif formt == "wif":
        return _decode(b58check_to_bin(priv), 256)
    elif formt == "wif_compressed":
        return _decode(b58check_to_bin(priv)[:32], 256)
    else:
        raise Exception("WIF does not represent privkey")


def from_jacobian(p):
    z = inv(p[2], P)
    return ((p[0] * z**2) % P, (p[1] * z**3) % P)


def jacobian_double(p):
    if not p[1]:
        return (0, 0, 0)
    ysq = (p[1] ** 2) % P
    S = (4 * p[0] * ysq) % P
    M = (3 * p[0] ** 2 + A * p[2] ** 4) % P
    nx = (M**2 - 2 * S) % P
    ny = (M * (S - nx) - 8 * ysq**2) % P
    nz = (2 * p[1] * p[2]) % P
    return (nx, ny, nz)


def jacobian_multiply(a, n):  # NOQA: C901
    if a[1] == 0 or n == 0:
        return (0, 0, 1)
    if n == 1:
        return a
    if n < 0 or n >= N:
        return jacobian_multiply(a, n % N)
    if (n % 2) == 0:
        return jacobian_double(jacobian_multiply(a, n // 2))
    if (n % 2) == 1:
        return jacobian_add(jacobian_double(jacobian_multiply(a, n // 2)), a)


def jacobian_add(p, q):
    if not p[1]:
        return q
    if not q[1]:
        return p
    U1 = (p[0] * q[2] ** 2) % P
    U2 = (q[0] * p[2] ** 2) % P
    S1 = (p[1] * q[2] ** 3) % P
    S2 = (q[1] * p[2] ** 3) % P
    if U1 == U2:
        if S1 != S2:
            return (0, 0, 1)
        return jacobian_double(p)
    H = U2 - U1
    R = S2 - S1
    H2 = (H * H) % P
    H3 = (H * H2) % P
    U1H2 = (U1 * H2) % P
    nx = (R**2 - H3 - 2 * U1H2) % P
    ny = (R * (U1H2 - nx) - S1 * H3) % P
    nz = (H * p[2] * q[2]) % P
    return (nx, ny, nz)


def to_jacobian(p):
    o = (p[0], p[1], 1)
    return o


def fast_multiply(a, n):
    return from_jacobian(jacobian_multiply(to_jacobian(a), n))


def inv(a, n):
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def hash_to_int(x):
    if len(x) in [40, 64]:
        return _decode(x, 16)
    return _decode(x, 256)
