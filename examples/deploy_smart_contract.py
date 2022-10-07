"""Deploy a smart contract."""

import eospyo

setcode_data = [
    # data to set wasm file to account me.wam
    eospyo.Data(
        name="account",
        value=eospyo.types.Name("me.wam"),
    ),
    eospyo.Data(
        name="vmtype",
        value=eospyo.types.Uint8(0),  # almost always set to 0, has to be set
    ),
    eospyo.Data(
        name="vmversion",
        value=eospyo.types.Uint8(0),  # almost always set to 0, has to be set
    ),
    eospyo.Data(
        name="code",  # select "code" field to set a wasm file
        value=eospyo.types.Wasm(
            eospyo.types.load_bin_from_path("test_contract/test_contract.zip")
        ),  # path from current directory to wasm file
    ),
]

setabi_data = [
    eospyo.Data(
        name="account",
        value=eospyo.types.Name("me.wam"),
    ),
    eospyo.Data(
        name="abi",  # select "abi" field to set a abi file
        value=eospyo.types.Abi(
            eospyo.types.load_dict_from_path("test_contract/test_contract.abi")
        ),  # path from current directory to abi file
    ),
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

setcode_action = eospyo.Action(
    account="eosio",
    name="setcode",
    data=setcode_data,
    authorization=[auth],
)

setabi_action = eospyo.Action(
    account="eosio",
    name="setabi",
    data=setabi_data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[setabi_action, setcode_action])

net = eospyo.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
