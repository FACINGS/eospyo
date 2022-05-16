Minimalist python library to interact with eosio blockchain networks


# What is it?
**eospyo** is a python library to interact with EOSIO blockchains.  
Its main focus are server side applications.  
This library is heavily influenced (and still uses some pieces of code from) by [µEOSIO](https://github.com/EOSArgentina/ueosio). Many thanks to them for the astonishing job!  


# Main features
- <ins>Send transactions</ins>  
Its main usage today is to send transactions to the blockchain
- <ins>Statically typed</ins>  
This library enforces and verifies types and values.
- <ins>Serialization</ins>  
**eospyo** serializes the transaction before sending to the blockchain. 
- <ins>Paralellization</ins>  
Although python has the [GIL](https://realpython.com/python-gil/) we try to make as easier as possible to paralellize the jobs.  
All data is as immutable and all functions are as pure as we can make them.  


# Stability
This work is in alpha version. That means that we make constant breaking changes to its api.  
Also there are known (and, of course unknown) bugs and various limitations.  
Given that, we at [FACINGS](https://facings.io/) have been using this library in production for some few months now.  
However we'd advise for you to fix its version when deploying to prod.  


# Using
Just `pip install eospyo` and play around.  
(we don't support, and have no plans to support [conda](https://docs.conda.io/en/latest/))  
Rather then starting with long docs, just a simple example:  


## Use Send Message action
```
import eospyo


print("Create Transaction")
data=[
    eospyo.Data(
        name="from",
        value=eospyo.types.Name("me.wam"), 
    ),
    eospyo.Data(
        name="message",
         value=eospyo.types.String("hello from eospyo"),
    ),
]

auth = eospyo.Authorization(actor="me.wam", permission="active")

action = eospyo.Action(
    account="me.wam", # this is the contract account
    name="sendmsg", # this is the action name
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

print("Link transaction to the network")
net = eospyo.WaxTestnet()  # this is an alias for a testnet node
# notice that eospyo returns a new object instead of change in place
linked_transaction = raw_transaction.link(net=net)


print("Sign transaction")
key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)


print("Send")
resp = signed_transaction.send()

print("Printing the response")
resp_fmt = json.dumps(resp, indent=4)
print(f"Response:\n{resp_fmt}")
```

There are some other examples [here](./examples)


# Known bugs
### Keys not working
- Some keys are reported to not work. However this error was not replicated and the cause remains unknown. If you can share a key pair that is not working it would be very helpful.
### multi-byte utf-8 characters can not be serialized
- Serialization of multi-byte utf-8 characters is somewhat unpredictable in the current implementation, therfore any String input containing multi-utf8 byte characters will be blocked for the time being.


# Contributing
All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.  
If you find a bug, just open a issue with a tag "BUG".  
If you want to request a new feature, open an issue with a tag "ENH" (for enhancement).  
If you feel like that our docs could be better, please open one with a tag "DOC".  
Although we have the next few steps already planned, we are happy to receive the community feedback to see where to go from there.  


### Development
If you want to develop for **eospyo**, here are some tips for a local development environment.
We'll be more then happy to receive PRs from the community.
Also we're going full [Black](https://black.readthedocs.io/en/stable/) and enforcing [pydocstyle](http://www.pydocstyle.org/en/stable/) and [isort](https://pypi.org/project/isort/) (with the limitations described in the .flake8 file)

#### Setup
Create a virtual env
Ensure the dependencies are met:
```
pip install poetry
poetry install
```

#### Run tests
The tests are run against a local network.  
Before running the tests you'll need to `docker-compose up` to create the local network, users and contracts used in the tests.  
When ready, just:
```
pytest
```



