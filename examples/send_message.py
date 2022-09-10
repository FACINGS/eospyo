"""Send a message."""


import eospyo


data = [
    # Not specifying an account with the "to" field will send the message to the same account sending it in the "from" field
    eospyo.Data(name="from", value=eospyo.types.Name("me.wam")),
    eospyo.Data(
        name="message",
        value=eospyo.types.String("hello from eospyo"), # String specified for message type, type must be specificed
    ),
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

action = eospyo.Action(
    account="me.wam",
    name="sendmsg",
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

net = eospyo.Local()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
