"""Take cpu to a account."""

import eospyo

data = [
    eospyo.Data(
        name="from", 
        value=eospyo.types.Name("me.wam")
    ),
    eospyo.Data(
        name="receiver", 
        value=eospyo.types.Name("me.wam")
    ),
    eospyo.Data(
        name="stake_cpu_quantity",
        value=eospyo.types.Asset("15.00000000 WAX"),
    ),
    eospyo.Data(
        name="stake_net_quantity",
        value=eospyo.types.Asset("30.00000000 WAX"),
    ),
    eospyo.Data(
        name="transfer",
        value=eospyo.types.Bool(False),
    )
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

action = eospyo.Action(
    account="eosio",
    name="delegatebw",
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

net = eospyo.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
