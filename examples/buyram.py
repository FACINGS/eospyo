"""Buy some ram to some account."""


import eospyo

data = [
    # in this case the account me.wam is buying ram for itself
    eospyo.Data(name="payer", value=eospyo.types.Name("me.wam")),
    eospyo.Data(name="receiver", value=eospyo.types.Name("me.wam")),
    eospyo.Data(
        name="quant", # Selects the 'quant' field in this action, must be a valid field in the action
        value=eospyo.types.Asset("5.00000000 WAX"), # Asset type must be specified as quant requires the amount and currency type, which Asset includes
    ),
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

action = eospyo.Action(
    account="eosio",
    name="buyram",
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

net = eospyo.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
