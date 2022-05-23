"""Transaction, Authorization and Action classes."""


import datetime as dt
import hashlib
import json
from typing import List

import pydantic
import ueosio

from . import types
from .net import Net


class Authorization(pydantic.BaseModel):
    """
    Authorization to be used in Action.

    actor: str
    permission: str
    """

    actor: pydantic.constr(min_length=1, max_length=13)
    permission: pydantic.constr(min_length=1, max_length=13)

    def __bytes__(self):
        bytes_ = b""
        account_name = types.Name(self.actor)
        bytes_ += bytes(account_name)
        permission = types.Name(self.permission)
        bytes_ += bytes(permission)
        return bytes_

    class Config:
        extra = "forbid"
        frozen = True


class Data(pydantic.BaseModel):
    """
    Data to be used in actions.

    name: the data field name
    value: the typed value (types.EosioType) of the data
    """

    name: str
    value: types.EosioType

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            if isinstance(args[0], dict):
                self = self.parse_obj(args[0])
                return
        super().__init__(*args, **kwargs)

    @classmethod
    def parse_obj(self, obj):
        for field in ["name", "type", "value"]:
            if field not in obj:
                msg = f"Field {field} expected. {obj}"
                raise ValueError(msg)
        if len(obj) != 3:
            msg = (
                f"Object with lenght 3 was expected, but {len(obj)} "
                f"found: {obj}"
            )
            raise ValueError(msg)
        name = obj["name"]
        type_str = obj["type"]
        value_raw = obj["value"]
        type_obj = types.from_string(type_str)
        value = type_obj(value_raw)
        return Data(name=name, value=value)

    def dict(self):
        d = dict(
            name=self.name,
            type=self.value.__class__.__name__,
            value=self.value.value,
        )
        return d

    def json(self):
        d = self.dict()
        j = json.dumps(d)
        return j

    def __bytes__(self):
        return bytes(self.value)

    class Config:
        extra = "forbid"
        frozen = True


class Action(pydantic.BaseModel):
    """
    Action to be used in Transaction.

    account: str
    name: str
    data: list[Data]
    authorization: list[Action]
    """

    account: pydantic.constr(max_length=13)
    name: str
    authorization: pydantic.conlist(Authorization, min_items=1, max_items=10)
    data: List[Data]

    @pydantic.validator("data", "authorization")
    def transform_to_tuple(cls, v):
        new_v = tuple(v)
        return new_v

    # returns a LinkedAction with current values and a specificed net value
    def link(self, net: Net):
        return LinkedAction(
            account=self.account,
            name=self.name,
            authorization=self.authorization,
            data=self.data,
            net=net,
        )

    def __bytes__(self):
        name = self.__class__.__name__
        raise TypeError(f"cannot convert '{name}' object to bytes")

    class Config:
        extra = "forbid"
        frozen = True
        arbitrary_types_allowed = True


class LinkedAction(Action):
    """
    Action to be used in LinkedTransaction.

    account: str
    name: str
    data: list[Data]
    authorization: list[Authorization]
    """

    account: pydantic.constr(max_length=13)
    name: str
    authorization: pydantic.conlist(Authorization, min_items=1, max_items=10)
    data: List[Data]
    net: Net

    def __bytes__(self):
        bytes_ = b""
        account_name = types.Name(value=self.account)
        bytes_ += bytes(account_name)
        action_name = types.Name(value=self.name)
        bytes_ += bytes(action_name)

        auth_bytes = [bytes(a) for a in self.authorization]
        auth = types.Array(type_=types.Bytes, values=auth_bytes)
        bytes_ += bytes(auth)

        data_bytes = b""
        for d in self.data:
            data_bytes += bytes(d)
        data_bytes = data_bytes.hex()
        data_bytes_list = []
        for i in range(0, len(data_bytes), 2):
            data_bytes_list.append(data_bytes[i : i + 2])  # NOQA: E203
        data_bytes_list = [bytes.fromhex(b) for b in data_bytes_list]
        data = types.Array(type_=types.Bytes, values=data_bytes_list)

        bytes_ += bytes(data)

        return bytes_


class Transaction(pydantic.BaseModel):
    """
    Raw Transaction. It can't be sent to the blockchain.

    It becomes a LinkedTransaction when a Net is linked

    actions: list[Action]
    delay_sec: int = 0
    max_cpu_usage_ms: int = 0
    chain_id: Optional[str]
    """

    actions: pydantic.conlist(Action, min_items=1, max_items=10)
    expiration_delay_sec: pydantic.conint(ge=0) = 600
    delay_sec: pydantic.conint(ge=0) = 0
    max_cpu_usage_ms: pydantic.conint(ge=0) = 0
    max_net_usage_words: pydantic.conint(ge=0) = 0

    @pydantic.validator("actions")
    def _transform_to_tuple(cls, v):
        new_v = tuple(v)
        return new_v

    # used to link transaction to a specified network (net)
    # gets required info from net then returns a LinkedTransaction
    def link(self, *, net: Net):  # block_id: str, chain_id: str):
        net_info = net.get_info()
        block_id = net_info["last_irreversible_block_id"]
        chain_id = net_info["chain_id"]

        ref_block_num, ref_block_prefix = ueosio.get_tapos_info(
            block_id=block_id
        )
        expiration = dt.datetime.utcnow() + dt.timedelta(
            seconds=self.expiration_delay_sec
        )

        new_trans = LinkedTransaction(
            # load every action as a linkedAction with the net passed in
            actions=[a.link(net) for a in self.actions],
            net=net,
            expiration_delay_sec=self.expiration_delay_sec,
            delay_sec=self.delay_sec,
            max_cpu_usage_ms=self.max_cpu_usage_ms,
            max_net_usage_words=self.max_net_usage_words,
            chain_id=chain_id,
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
        )

        return new_trans

    class Config:
        extra = "forbid"
        frozen = True
        arbitrary_types_allowed = True


class LinkedTransaction(Transaction):
    """
    Linked transaction. It can't be sent to the blockchain.

    It becomes a SignedTransaction when you sign it.
    """

    actions: pydantic.conlist(LinkedAction, min_items=1, max_items=10)
    net: Net
    chain_id: str
    ref_block_num: str
    ref_block_prefix: str
    expiration: dt.datetime

    def __bytes__(self):
        bytes_ = b""
        bytes_ += bytes(types.UnixTimestamp(self.expiration))
        bytes_ += bytes(types.Uint16(self.ref_block_num))
        bytes_ += bytes(types.Uint32(self.ref_block_prefix))
        bytes_ += bytes(types.Varuint32(self.max_net_usage_words))
        bytes_ += bytes(types.Uint8(self.max_cpu_usage_ms))
        bytes_ += bytes(types.Varuint32(self.delay_sec))
        # context_free_actions
        bytes_ += bytes(types.Array(type_=types.Int8, values=[]))

        actions_bytes = [bytes(act) for act in self.actions]
        actions = types.Array(type_=types.Bytes, values=actions_bytes)
        bytes_ += bytes(actions)

        # transaction_extensions
        bytes_ += bytes(types.Array(type_=types.Int8, values=[]))

        return bytes_

    def id(self):
        hash256 = hashlib.sha256()
        hash256.update(bytes(self))
        hash256_digest = hash256.digest()
        return hash256_digest.hex()

    def sign(self, key: str):
        signs = []
        if hasattr(self, "signatures"):
            signs = list(self.signatures)

        chain_bytes = bytes.fromhex(self.chain_id)
        trans_bytes = bytes(self)
        zero_bytes = bytes.fromhex("0" * 64)
        bytes_ = chain_bytes + trans_bytes + zero_bytes

        signature = sign_bytes(bytes_, key)
        signs.append(signature)
        trans = SignedTransaction(
            net=self.net,
            actions=self.actions,
            expiration_delay_sec=self.expiration_delay_sec,
            delay_sec=self.delay_sec,
            max_cpu_usage_ms=self.max_cpu_usage_ms,
            max_net_usage_words=self.max_net_usage_words,
            chain_id=self.chain_id,
            ref_block_num=self.ref_block_num,
            ref_block_prefix=self.ref_block_prefix,
            expiration=self.expiration,
            signatures=tuple(signs),
        )
        return trans


def sign_bytes(bytes_: bytes, key: str) -> str:
    nonce = 0
    sha256 = hashlib.sha256()
    sha256.update(bytes_)
    while True:
        v, r, s = ueosio.utils.ecdsa_raw_sign_nonce(
            sha256.digest(), key, nonce
        )
        if ueosio.utils.is_canonical(r, s):
            signature = "00%02x%064x%064x" % (v, r, s)
            break
        nonce += 1

    ds = ueosio.DataStream(bytes.fromhex(signature))
    signature = ds.unpack_signature()

    return signature


class SignedTransaction(LinkedTransaction):
    """
    Signed transaction. You can send it to the blockchain.

    Also you can sign it again.
    """

    signatures: pydantic.conlist(str, min_items=1, max_items=10)

    @pydantic.validator("signatures")
    def _transform_to_tuple(cls, v):
        new_v = tuple(v)
        return new_v

    def pack(self):
        bytes_ = bytes(self)
        return bytes_.hex()

    def send(self):
        resp = self.net.push_transaction(transaction=self)
        return resp


__all__ = [
    "Action",
    "Authorization",
    "Data",
    "Transaction",
    "LinkedTransaction",
    "SignedTransaction",
    "LinkedAction",
]
