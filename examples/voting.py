"""Vote to a nice blockproducer ;) ."""

import eospyo


data = [
    eospyo.Data(
        name="voter",
        value=eospyo.types.Name("me.wam"),
    ),
    eospyo.Data(
        name="proxy",
        value=eospyo.types.Name(""),
    ),
    eospyo.Data(
        name="producers",
        value=eospyo.types.Array(type_=eospyo.types.Name, values=["eosiodetroit"]),
    ),
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

action = eospyo.Action(
    account="eosio",
    name="voteproducer",
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

net = eospyo.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
