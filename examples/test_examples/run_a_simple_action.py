"""Buy some ram to some account."""


import eospyo
import json

#old in-house data initialization brought back due to backend serialization being brought back
data = [
    eospyo.Data(
        name="worker",
        value=eospyo.types.Name("open.facings"),
    ),
    eospyo.Data(
        name="nonce",
        value=eospyo.types.Uint64(123),
    ),
]

#everything else has the same syntax as current examples
auth = eospyo.Authorization(actor="youraccount", permission="active")

action = eospyo.Action(
    account="open.facings",
    name="runjobs",
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

net = eospyo.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()

print("Printing the response")
resp_fmt = json.dumps(resp, indent=4)
print(f"Response:\n{resp_fmt}")

