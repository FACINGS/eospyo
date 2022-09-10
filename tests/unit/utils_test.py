import pytest

import eospyo

input_key_expected = [
    (b"a", "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3", "SIG_K1_HMzWEbzA8LXD5CyYHE45CeMMpCXvEy531ntG1jeio9kRHjAHCrtWoV6SFcgdb32rEqEChsW2ne7dakztmJ6JuCMMcziZPd"),  # NOQA: BLK100, E501
    (b"b", "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3", "SIG_K1_HQK8172obRP5BVdJHu9nqnvMvfWigYQUz9ZzWU7TPG7i6kYmD5DMgG28wTSu1HtjibnNusL4qsFq4TYSqYQtapSdUrPtuM"),  # NOQA: E501
    (b"a" * 100, "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3", "SIG_K1_GoG4EmmHp91YHosmeAJ1yqGKUZL5H5nJ3ibgU4GPDEB7mYpKiqBwxVoJCVXFMYg35paDvePCWoJNrQdAp3hewaUnxwz5rt"),  # NOQA: E501
    (b"a", "5HsVgxhxdL9gvgcAAyCZSWNgtLxAhGfEX2YU98w6QSkePoVvPNK", "SIG_K1_GhZ9nT4VV2c9BchufRGH8QDB7BAPUoSfzYxHW7AYxCmAzE8MeNkTLUi9hDzqXuMYx2NoirtD835q8rAYNty5qDe1PQDaZM"),  # NOQA: BLK100, E501
    (b"b", "5HsVgxhxdL9gvgcAAyCZSWNgtLxAhGfEX2YU98w6QSkePoVvPNK", "SIG_K1_HQZH1bcA8MYHun9uKi1WQSY9fQ65f24uV6zRNc43XZsnDWUtKYSAWffXndVGk2VFTuwCZZ9nJetuEsn1DfHi6sR616UED8"),  # NOQA: E501
    (b"a" * 100, "5HsVgxhxdL9gvgcAAyCZSWNgtLxAhGfEX2YU98w6QSkePoVvPNK", "SIG_K1_Ghu723QqAz23MTDCw4gLGKtWQceU6kTu1Z9HCsURZueSTYhwLMTkw9UduAVqxNfCkFBV5iv3RjqfzsDEQ7Kpe42rtqJJ9t"),  # NOQA: E501
]


@pytest.mark.parametrize("input_,key,expected", input_key_expected)
def test_sign_bytes(input_, key, expected):
    output = eospyo.utils.sign_bytes(bytes_=input_, key=key)
    assert output == expected


def test_sign_bytes_with_empty_message_raise_value_error():
    key = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
    with pytest.raises(ValueError):
        eospyo.utils.sign_bytes(bytes_="", key=key)


def test_sign_bytes_with_string_raises_type_error():
    key = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
    with pytest.raises(TypeError):
        eospyo.utils.sign_bytes(bytes_="a", key=key)


bogus_private_key = ["", "a", "a" * 100, "a" * 1000]


@pytest.mark.parametrize("key", bogus_private_key)
def test_sign_bytes_with_improper_key_format(key):
    with pytest.raises(ValueError):
        eospyo.utils.sign_bytes(bytes_=b"a", key=key)
