"""Send a message."""


import eospyo


data=[
        eospyo.Data(name="from", value=eospyo.types.Name("me.wam")),
        eospyo.Data(name="message", value=eospyo.types.String("hello from eospyo"),),
    ]

#everything else has the same syntax as current examples
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

