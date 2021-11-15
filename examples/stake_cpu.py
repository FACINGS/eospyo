"""Take cpu to a account."""

import eospyo

data = {
    "from": "me.wam",
    "receiver": "me.wam",
    "amount": "45.00000000 WAX",
    "stake_cpu_quantity": "15.00000000 WAX",
    "stake_net_quantity": "30.00000000 WAX",
    "transfer": False,
}

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
