"""Transfer some WAX to a receiver account."""

import eospyo

data = [
    # In this case the account me.wam is transferring to account 'reciever'
    eospyo.Data(name="from", value=eospyo.types.Name("me.wam")),
    eospyo.Data(name="to", value=eospyo.types.Name("receiver")),
    eospyo.Data(
        name="quantity", # Selects the 'quantity' field in this action, must be a valid field in the action
        value=eospyo.types.Asset("55.00000000 WAX"), # Asset type must be specified as 'quantity' requires the amount and currency type, which Asset includes
    ),
    eospyo.Data(
        name="memo", # Selects the 'memo' field in this action, just an extra message with the transfer
        value=eospyo.types.String("Trying EosPyo"), # String type is used for memo
    ),
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

action = eospyo.Action(
    account="eosio.token",
    name="transfer",
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

net = eospyo.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
