"""Eosio data types."""

import calendar
import datetime as dt
import re
import struct
import sys
from abc import ABC, abstractmethod

import pydantic


class EosioType(pydantic.BaseModel, ABC):
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            super().__init__(value=args[0])
        else:
            super().__init__(*args, **kwargs)

    @pydantic.validator("value", pre=True, check_fields=False)
    def check_if_same_type(cls, v):
        if type(v) is cls:
            return v.value
        return v

    @abstractmethod
    def __bytes__(self):
        """Convert instance to bytes."""

    @abstractmethod
    def from_bytes(self):
        """Create instance from bytes."""

    def __len__(self):
        """Lenght of value in bytes."""
        bytes_ = bytes(self)
        return len(bytes_)

    class Config:
        extra = "forbid"
        frozen = True


class UnixTimestamp(EosioType):
    """
    Serialize a datetime.

    Precision is in seconds
    Considers UTC time
    """

    value: dt.datetime

    @pydantic.validator("value")
    def remove_everything_bellow_seconds(cls, v):
        new_v = v.replace(microsecond=0)
        return new_v

    def __bytes__(self):
        unix_secs = calendar.timegm(self.value.timetuple())
        uint32_secs = Uint32(value=unix_secs)
        bytes_ = bytes(uint32_secs)
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_):
        uint32_secs = Uint32.from_bytes(bytes_)
        datetime = dt.datetime.utcfromtimestamp(uint32_secs.value)
        return cls(value=datetime)


class Bool(EosioType):
    value: bool

    def __bytes__(self):
        return b"\x01" if self.value else b"\x00"

    @classmethod
    def from_bytes(cls, bytes_):
        return cls(value=int(bytes_[:1].hex(), 16))


class String(EosioType):
    value: str

    def __bytes__(self):
        bytes_ = self.value.encode("utf8")
        length = len(bytes_)
        bytes_ = bytes(Varuint32(value=length)) + bytes_
        return bytes_

    @pydantic.validator("value")
    def must_not_contain_multi_utf_char(cls, v):
        if len(v) < len(v.encode("utf8")):
            msg = (
                f'Input "{v}" has a multi-byte utf character in it, '
                "currently eospyo does not support serialization of "
                "multi-byte utf characters."
            )
            raise ValueError(msg)
        return v

    @classmethod
    def from_bytes(cls, bytes_):
        size = Varuint32.from_bytes(bytes_)
        start = len(size)
        string_bytes = bytes_[start : start + size.value]  # NOQA: E203
        value = string_bytes.decode("utf8")
        return cls(value=value)


class Asset(EosioType):
    """
    Serialize a Asset.

    serializes an amount (can be a float value) and currency name together
    uses Symbol type to serialize percision and name of currency,
    uses Uint64 type to serialize amount
    amount and name are seperated by one space
    example: 50.100000 WAX
    """

    value: str

    def get_name(self):
        """
        Extract the name from a raw Asset string.

        example: "WAX" from Asset string "99.1000000 WAX"
        """
        stripped_value = self.value.strip()
        return stripped_value.split(" ")[1]

    def get_int_digits(self):
        """
        Extract the integer digits (digits before the decimal).

        from raw Asset string
        example: "99" from Asset string "99.1000000 WAX"
        """
        stripped_value = self.value.strip()
        pos = 0
        int_digits = ""

        # check for negative sign
        if stripped_value[pos] == "-":
            int_digits += "-"
            pos += 1

        curr_char = stripped_value[pos]

        # get amount value
        while (
            pos < len(stripped_value) and curr_char >= "0" and curr_char <= "9"
        ):
            int_digits += curr_char
            pos += 1
            curr_char = stripped_value[pos]

        return int_digits

    def get_frac_digits(self):
        """
        Extract the decimal digits as integers (digits after the decimal).

        example: "1000000" from Asset string "99.1000000 WAX"
        """
        stripped_value = self.value.strip()
        pos = 0
        precision = 0
        frac_digits = ""
        curr_char = 0

        if "." in stripped_value:
            pos = stripped_value.index(".") + 1
            curr_char = stripped_value[pos]
            while (
                pos < len(stripped_value)
                and curr_char >= "0"  # noqa: W503
                and curr_char <= "9"  # noqa: W503
            ):
                frac_digits += curr_char
                pos += 1
                curr_char = stripped_value[pos]
                precision += 1

        else:
            return ""

        return frac_digits

    def get_precision(self):
        """
        Get the precision (number of digits after decimal).

        example: "7" from Asset string "99.1000000 WAX"
        """
        return len(self.get_frac_digits())

    def __bytes__(self):

        amount = Uint64(int(self.get_int_digits() + self.get_frac_digits()))
        name = self.get_name()
        symbol = Symbol(str(self.get_precision()) + "," + name)

        amount_bytes = bytes(amount)
        symbol_bytes = bytes(symbol)

        return amount_bytes + symbol_bytes

    @classmethod
    def from_bytes(cls, bytes_):
        amount_bytes = bytes_[:8]  # get first 8 bytes
        asset_precision = bytes_[8]  # (amount of decimal places)
        amount = str(
            struct.unpack("<Q", amount_bytes)[0]
        )  # amount with decimal values (no decimal splitting yet)
        # get name (currency) from Symbol
        name = str(Symbol.from_bytes(bytes_[8:])).split(",")[1][:-1]
        if asset_precision == 0:
            value = amount + " " + name
        else:
            value = (
                amount[:-asset_precision]
                + "."  # noqa: W503
                + amount[asset_precision + 1 :]  # noqa: W503, E203
                + " "  # noqa: W503
                + name  # noqa: W503
            )  # combine everything and place decimal in correct position
        return cls(value=value)

    @pydantic.validator("value")
    def amount_must_be_in_the_valid_range(cls, v):
        value_list = str(v).strip().split(" ")
        if len(value_list) != 2:
            msg = (
                f'Input "{v}" must have exactly one space in between '
                "amount and name"
            )
            raise ValueError(msg)
        return v

    @pydantic.validator("value")
    def check_for_frac_digit_if_decimal_exists(cls, v):
        stripped_value = v.strip()
        if "." in stripped_value:
            pos = stripped_value.index(".") + 1
            curr_char = stripped_value[pos]
            if (
                pos < len(stripped_value)
                and curr_char >= "0"  # noqa: W503
                and curr_char <= "9"  # noqa: W503
            ):
                return v
            else:
                msg = (
                    "decimal provided but no fractional digits were provided."
                )
                raise ValueError(msg)
        return v

    @pydantic.validator("value", allow_reuse=True)
    def check_if_amount_is_valid(cls, v):
        stripped_value = v.strip()
        amount = float(stripped_value.split(" ")[0])
        if amount < 0 or amount > 18446744073709551615:
            msg = f'amount "{amount}" must be between 0 and ' "2^64 inclusive."
            raise ValueError(msg)
        return v

    @pydantic.validator("value", allow_reuse=True)
    def check_if_name_is_valid(cls, v):
        stripped_value = v.strip()
        name = stripped_value.split(" ")[1]
        match = re.search("^[A-Z]{1,7}$", name)
        if not match:
            msg = f'Input "{name}" must be A-Z and between 1 to 7 characters.'
            raise ValueError(msg)
        return v


class Symbol(EosioType):
    """
    Serialize a Symbol.

    serializes a percision and currency name together
    precision is used to indicate how many decimals there
    are in an Asset type amount
    precision and name are seperated by a commma
    example: 1,WAX
    """

    value: str

    @pydantic.validator("value", allow_reuse=True)
    def name_must_be_of_valid_length(cls, v):
        name = v.split(",")[1]
        match = re.search("^[A-Z]{1,7}$", name)
        if not match:
            msg = f'Input "{name}" must be A-Z and between 1 to 7 characters.'
            raise ValueError(msg)
        return v

    @pydantic.validator("value", allow_reuse=True)
    def precision_must_be_in_the_valid_range(cls, v):
        precision = int(v.split(",")[0])
        if precision < 0 or precision > 16:
            msg = (
                f'precision "{precision}" must be between 0 and '
                "16 inclusive."
            )
            raise ValueError(msg)
        return v

    def __bytes__(self):
        precision = int(self.value.split(",")[0])
        precision_bytes_ = struct.pack("<B", (precision & 0xFF))
        bytes_ = precision_bytes_
        name = self.value.split(",")[1]
        name_bytes_ = name.encode("utf8")
        bytes_ += name_bytes_
        leftover_byte_space = len(name) + 1
        while (
            leftover_byte_space < 8
        ):  # add null bytes in remaining empty space
            bytes_ += struct.pack("<B", 0)
            leftover_byte_space += 1
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_):
        bytes_len = len(bytes_)
        precision = ""
        name = ""
        for i in range(bytes_len):
            if chr(bytes_[i]).isupper():
                precision = str(bytes_[0])
                name_bytes = bytes_[i:]  # name is all bytes after precision
                for k in range(1, len(name_bytes) + 1):
                    if not chr(bytes_[k]).isupper():
                        name_bytes = name_bytes[
                            : k - 1
                        ]  # name only goes up to the last upper case character
                name = name_bytes.decode("utf8")
                break

        value = precision + "," + name
        return cls(value=value)


class Bytes(EosioType):
    value: bytes

    def __bytes__(self):
        return self.value

    @classmethod
    def from_bytes(cls, bytes_):
        return cls(value=bytes_)


class Array(EosioType):
    values: tuple
    type_: type

    @pydantic.validator("type_")
    def must_be_subclass_of_eosio(cls, v):
        if not issubclass(v, EosioType):
            raise ValueError("Type must be subclass of EosioType")
        return v

    @pydantic.root_validator(pre=True)
    def all_must_satisfy_type_value(cls, all_values):
        type_ = all_values["type_"]
        values = all_values["values"]
        if len(values) >= 1:
            values = tuple(type_(v) for v in values)
        else:
            values = tuple()
        all_values["values"] = values
        return all_values

    def __bytes__(self):
        bytes_ = b""
        length = Varuint32(len(self.values))
        bytes_ += bytes(length)
        for value in self.values:
            bytes_ += bytes(value)
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_, type_):
        length = Varuint32.from_bytes(bytes_)
        bytes_ = bytes_[len(length) :]  # NOQA: E203
        values = []
        for n in range(length.value):
            value = type_.from_bytes(bytes_)
            values.append(value.value)
            bytes_ = bytes_[len(value) :]  # NOQA: E203
        return cls(values=values, type_=type_)

    def __getitem__(self, index):
        return Array(values=self.values[index], type_=self.type_)


class Name(EosioType):
    # regex = has at least one "non-dot" char
    value: pydantic.constr(
        max_length=13,
        regex=r"^[\.a-z1-5]*[a-z1-5]+[\.a-z1-5]*$|^(?![\s\S])",  # NOQA: F722
    )

    def __eq__(self, other):
        """Equality diregards dots in names."""
        if type(other) != type(self):
            return False
        return self.value.replace(".", "") == other.value.replace(".", "")

    @pydantic.validator("value")
    def last_char_restriction(cls, v):
        if len(v) == 13:
            allowed = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "."}
            if v[-1] not in allowed:
                msg = (
                    "When account name is 13 char long, last char must be "
                    f'in range a-z or ".". "{v[-1]}" found.'
                )
                raise ValueError(msg)
        return v

    def __bytes__(self):
        value_int = self.string_to_uint64(self.value)
        uint64 = Uint64(value=value_int)
        return bytes(uint64)

    @classmethod
    def from_bytes(cls, bytes_):
        uint64 = Uint64.from_bytes(bytes_)
        value_str = cls.uint64_to_string(uint64.value, strip_dots=True)
        return cls(value=value_str)

    @classmethod
    def char_to_symbol(cls, c):
        if c >= ord("a") and c <= ord("z"):
            return (c - ord("a")) + 6
        if c >= ord("1") and c <= ord("5"):
            return (c - ord("1")) + 1
        return 0

    @classmethod
    def string_to_uint64(cls, s):
        if len(s) > 13:
            raise Exception("invalid string length")
        name = 0
        i = 0
        while i < min(len(s), 12):
            name |= (cls.char_to_symbol(ord(s[i])) & 0x1F) << (
                64 - 5 * (i + 1)
            )
            i += 1
        if len(s) == 13:
            name |= cls.char_to_symbol(ord(s[12])) & 0x0F
        return name

    @classmethod
    def uint64_to_string(cls, n, strip_dots=False):
        charmap = ".12345abcdefghijklmnopqrstuvwxyz"
        s = bytearray(13 * b".")
        tmp = n
        for i in range(13):
            c = charmap[tmp & (0x0F if i == 0 else 0x1F)]
            s[12 - i] = ord(c)
            tmp >>= 4 if i == 0 else 5

        s = s.decode("utf8")
        if strip_dots:
            s = s.strip(".")
        return s


class Int8(EosioType):
    value: pydantic.conint(ge=-128, lt=128)

    def __bytes__(self):
        return struct.pack("<b", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<b", bytes_[:1])
        value = struct_tuple[0]
        return cls(value=value)


class Uint8(EosioType):
    value: pydantic.conint(ge=0, lt=256)  # 2 ** 8

    def __bytes__(self):
        return struct.pack("<B", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<B", bytes_[:1])
        value = struct_tuple[0]
        return cls(value=value)


class Uint16(EosioType):
    value: pydantic.conint(ge=0, lt=65536)  # 2 ** 16

    def __bytes__(self):
        return struct.pack("<H", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<H", bytes_[:2])
        value = struct_tuple[0]
        return cls(value=value)


class Uint32(EosioType):
    value: pydantic.conint(ge=0, lt=4294967296)  # 2 ** 32

    def __bytes__(self):
        return struct.pack("<I", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<I", bytes_[:4])
        value = struct_tuple[0]
        return cls(value=value)


class Uint64(EosioType):
    value: pydantic.conint(ge=0, lt=18446744073709551616)  # 2 ** 64

    def __bytes__(self):
        return struct.pack("<Q", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<Q", bytes_)
        value = struct_tuple[0]
        return cls(value=value)


class Varuint32(EosioType):
    value: pydantic.conint(ge=0, le=20989371979)

    def __bytes__(self):
        bytes_ = b""
        val = self.value
        while True:
            b = val & 0x7F
            val >>= 7
            b |= (val > 0) << 7
            uint8 = Uint8(value=b)
            bytes_ += bytes(uint8)
            if not val:
                break
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_):
        offset = 0
        value = 0
        for n, byte in enumerate(bytes_):
            partial_value = byte & 0x7F  # only the 7 first bits matter
            partial_value_offset = partial_value << offset
            value |= partial_value_offset
            offset += 7
            if n >= 8:
                break
            if not byte & 0x80:  # first bit (carry) off
                break
        return cls(value=value)


def _get_all_types():
    def is_eostype(class_):
        if isinstance(class_, type):
            if issubclass(class_, EosioType) and class_ is not EosioType:
                return True
        return False

    classes = list(sys.modules[__name__].__dict__.items())

    all_types = {
        name.lower(): class_ for name, class_ in classes if is_eostype(class_)
    }
    return all_types


_all_types = _get_all_types()


def from_string(type_: str) -> EosioType:
    type_ = type_.lower()
    try:
        class_ = _all_types[type_]
    except KeyError:
        types = list(_all_types.keys())
        msg = f"Type {type_} not found. List of available {types=}"
        raise ValueError(msg)
    return class_
