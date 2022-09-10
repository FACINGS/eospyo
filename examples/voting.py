"""Vote to a nice blockproducer ;) ."""

import eospyo


data = [
    # Specifices the voter account
    eospyo.Data(
        name="voter",
        value=eospyo.types.Name("me.wam"),
    ),
    # Specifices the proxy (can be empty)
    eospyo.Data(
        name="proxy",
        value=eospyo.types.Name(""),
    ),
    # Specifics the producers
    eospyo.Data(
        name="producers",
        # can vote for mutliple producers, so value is of type array
        # for Array type, need yo specify type of Array with '_type' and values of array in a list
        value=eospyo.types.Array(
            type_=eospyo.types.Name, values=["eosiodetroit"]
        ),
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
