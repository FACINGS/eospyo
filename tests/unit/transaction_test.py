import datetime as dt
import json

import pydantic
import pytest

import eospyo


def test_create_authorization_using_dict():
    auth = eospyo.Authorization.parse_obj(
        {"actor": "aaa", "permission": "active"}
    )
    assert isinstance(auth, eospyo.Authorization)


def test_create_authorization_using_keywords():
    auth = eospyo.Authorization(actor="aaa", permission="active")
    assert isinstance(auth, eospyo.Authorization)


def test_create_authorization_requires_actor_len_lt_13():
    with pytest.raises(pydantic.ValidationError):
        eospyo.Authorization(actor="a" * 14, permission="active")


def test_authorization_is_immutable(auth):
    with pytest.raises(TypeError):
        auth.actor = "bbb"


def test_create_data_from_dict():
    d = eospyo.Data.from_dict({"from": "user1"})
    assert isinstance(d, eospyo.Data)


def test_create_data_with_args():
    d = eospyo.Data(name="user1")
    assert isinstance(d, eospyo.Data)


def test_create_data_from_dict_return_name():
    d1 = eospyo.Data.from_dict({"name": "user1"})
    assert d1.name == "user1"


def test_data_to_dict():
    expected = {"name": "user1"}
    data = eospyo.Data.from_dict(expected)
    data_dict = data.dict()
    assert data_dict == expected


def test_create_data_from_dict_equals_from_args():
    d1 = eospyo.Data.from_dict({"name": "user1"})
    d2 = eospyo.Data(name="user1")
    assert d1 == d2


def test_data_hash_equality_with_same_keys_and_values():
    d1 = eospyo.Data.from_dict({"from": "user1"})
    d2 = eospyo.Data.from_dict({"from": "user1"})
    assert hash(d1) == hash(d2)


def test_data_equality_with_same_keys_and_values():
    d1 = eospyo.Data.from_dict({"from": "user1"})
    d2 = eospyo.Data.from_dict({"from": "user1"})
    assert d1 == d2


def test_data_equality_with_diff_keys():
    d1 = eospyo.Data.from_dict({"from": "user1"})
    d2 = eospyo.Data.from_dict({"from1": "user1"})
    assert d1 != d2


def test_data_equality_with_same_keys_but_diff_values():
    d1 = eospyo.Data.from_dict({"from": "user1"})
    d2 = eospyo.Data.from_dict({"from": "user2"})
    assert d1 != d2


def test_data_is_immutable():
    d = eospyo.Data.from_dict({"field": "user1"})
    with pytest.raises(TypeError):
        d.field = "sldkmcsd"


def test_create_action():
    auth = [eospyo.Authorization(actor="user2", permission="active")]
    data = {}

    action = eospyo.Action(
        account="user2",
        name="clear",
        data=data,
        authorization=auth,
    )

    assert isinstance(action, eospyo.Action)


def test_action_requirest_at_least_one_auth():
    with pytest.raises(pydantic.ValidationError):
        eospyo.Action(
            account="user2",
            name="clear",
            data={},
            authorization=[],
        )


def test_when_action_link_returns_linked_action(net):
    action = eospyo.Action(
        account="user2",
        name="sendmsg",
        data={
            "from": "user1",
            "message": "msg sent using eospyo",
        },
        authorization=[
            eospyo.Authorization(actor="user1", permission="active"),
        ],
    )
    linked_action = action.link(net=net)
    assert isinstance(linked_action, eospyo.LinkedAction)


@pytest.fixture
def action_clear():
    auth = [eospyo.Authorization(actor="user2", permission="active")]
    data = {}
    action = eospyo.Action(
        account="user2",
        name="clear",
        data=data,
        authorization=auth,
    )
    yield action


def test_action_fields_are_immutable(action_clear):
    immutables = (str, int, bool, float, tuple, eospyo.Data)
    for field_name in action_clear.__fields__:
        field = getattr(action_clear, field_name)
        assert isinstance(field, immutables)


def test_create_transaction(action_clear):
    trans = eospyo.Transaction(actions=[action_clear])
    assert isinstance(trans, eospyo.Transaction)


def test_when_link_raw_transaction_then_returns_linked_transaction(
    action_clear, net
):
    raw_trans = eospyo.Transaction(actions=[action_clear])
    linked_trans = raw_trans.link(net=net)
    assert isinstance(linked_trans, eospyo.LinkedTransaction)


def test_when_sign_linked_transaction_then_return_signed_transaction(
    action_clear, net
):
    raw_trans = eospyo.Transaction(actions=[action_clear])
    linked_trans = raw_trans.link(net=net)
    signed_trans = linked_trans.sign(
        key="5HsVgxhxdL9gvgcAAyCZSWNgtLxAhGfEX2YU98w6QSkePoVvPNK"
    )
    assert isinstance(signed_trans, eospyo.SignedTransaction)


# transaction serialization, id and signature


@pytest.fixture
def example_transaction(net):
    action = eospyo.LinkedAction(
        net=net,
        account="user2",
        name="sendmsg",
        data={
            "from": "user2",
            "message": "hello",
        },
        authorization=[
            eospyo.Authorization(actor="user2", permission="active"),
        ],
    )
    linked_trans = eospyo.LinkedTransaction(
        net=net,
        actions=[action],
        expiration_delay_sec=0,
        delay_sec=0,
        max_cpu_usage_ms=0,
        max_net_usage_words=0,
        chain_id=(
            "8a34ec7df1b8cd06ff4a8abbaa7cc50300823350cadc59ab296cb00d104d2b8f"
        ),
        ref_block_num=23631,
        ref_block_prefix=2938989125,
        expiration=dt.datetime(2021, 8, 30, 13, 3, 31),
    )
    yield linked_trans


def test_example_transaction_pack(example_transaction):
    expected = "23d72c614f5c456a2daf000000000100000000007115d6000000806199a6c20100000000007115d600000000a8ed32320e00000000007115d60568656c6c6f00"  # NOQA: E501
    print(f"expected = {expected}")
    assert bytes(example_transaction).hex() == expected


def test_example_transaction_id(example_transaction):
    expected = "1a634bb62717cb1a94f5312c7d369b95fe7ea3f1f955a8c1907a74cf0d4153d6"  # NOQA: E501
    assert example_transaction.id() == expected


def test_example_transaction_has_expected_signature(example_transaction):
    key = "5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp"
    signed_transaction = example_transaction.sign(key=key)
    expected = "SIG_K1_HMzTApq6UiSA7Ldr6mCKqPKQkrsmUknHiZi4HZt7HMz3ktHHMv4MuRTEUx9Za8VbB6NzcUFh35EBj4Y9wtVjw9qL3t4xYX"  # NOQA: E501
    assert signed_transaction.signatures[0] == expected


@pytest.fixture
def trans_signed(action_clear, net):
    raw_trans = eospyo.Transaction(actions=[action_clear])
    linked_trans = raw_trans.link(net=net)
    trans = linked_trans.sign(
        key="5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp",
    )
    yield trans


def test_signed_transaction_has_1_signature(trans_signed):
    assert len(trans_signed.signatures) == 1


def test_when_sign_signed_transaction_then_return_signed_transaction(
    trans_signed,
):
    trans2 = trans_signed.sign(
        key="5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp"
    )
    assert isinstance(trans2, eospyo.SignedTransaction)


def test_double_signed_transaction_has_2_signatures(
    trans_signed,
):
    trans2 = trans_signed.sign(
        key="5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp"
    )
    assert len(trans2.signatures) == 2


def test_when_send_example_transaction_then_returns_expired_transaction_error(
    net, example_transaction
):
    trans = example_transaction.sign(
        key="5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp"
    )
    resp = net.push_transaction(transaction=trans)
    assert resp["error"]["what"] == "Expired Transaction"


@pytest.mark.flaky(reruns=2)
def test_e2e_with_transaction_ok(net):
    data = {"from": "user2", "message": "hello"}
    trans = eospyo.Transaction(
        actions=[
            eospyo.Action(
                account="user2",
                name="sendmsg",
                data=data,
                authorization=[
                    eospyo.Authorization(actor="user2", permission="active")
                ],
            )
        ],
    )
    linked_trans = trans.link(net=net)
    signed_trans = linked_trans.sign(
        key="5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp"
    )
    resp = signed_trans.send()
    print(json.dumps(resp, indent=4))
    assert "transaction_id" in resp
    assert resp["transaction_id"] == signed_trans.id()
    assert "processed" in resp
    assert "receipt" in resp["processed"]
    assert "status" in resp["processed"]["receipt"]
    assert resp["processed"]["receipt"]["status"] == "executed"
    actions = resp["processed"]["action_traces"]
    assert len(actions) == 1
    assert actions[0]["act"]["data"] == data


def test_e2e_with_transaction_signed_with_the_wrong_key(net):
    data = {"from": "user2", "message": "I cant say hello"}
    trans = eospyo.Transaction(
        actions=[
            eospyo.Action(
                account="user2",
                name="sendmsg",
                data=data,
                authorization=[
                    eospyo.Authorization(actor="user2", permission="active")
                ],
            )
        ],
    )
    linked_trans = trans.link(net=net)
    signed_trans = linked_trans.sign(
        key="5Je7woBXuxQBkpxit35SHZMap9SdKZLoeVBRKxntoMq2NuuN1rL"  # wrong key
    )
    resp = signed_trans.send()
    assert "code" in resp
    assert resp["code"] == 500
    assert "error" in resp
    assert "details" in resp["error"]
    assert len(resp["error"]["details"]) == 1
