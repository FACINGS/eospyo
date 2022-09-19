# eosio key:
# EOS6Pzm1Gs1eH3AxEQvZZdX2a71zASiwJdUn93775a92cbqcJR7ZJ
# 5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3

# some extra keys, just in case:
#
# EOS5AvFzuUatd9ejnXKWWjjgjphGYRv3DSdpskkL3phC3q547kxCJ  # user1
# 5HsVgxhxdL9gvgcAAyCZSWNgtLxAhGfEX2YU98w6QSkePoVvPNK
#
# EOS5sRtLNDzsd9arp7J7qYSRRTcaLnRQFVkYtRuHn8tPeNS8D7DVM  # user2
# 5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp
#
# EOS7dwjRjyyVPTg4UQQ3WozRhFLmspew8SP8BgbpTjrEPYs1c1rHV  # eosio.token
# 5Je7woBXuxQBkpxit35SHZMap9SdKZLoeVBRKxntoMq2NuuN1rL
#
# EOS8EN2WjAsysGmagNmorihtv4wj5Mfzg1vvCQA1L6q4sN2X63BiK
# 5J4qVtzDXFv4bPCLcsTXD5TpUowHkMU1EU175BNo9kcGrUaPXDF
#
# EOS8kMyaN5jyaGbPu6jX4bTygusD8HkzAmjHsNE8GcCs9Bi7eFqV1
# 5KYm8W89NAx4wamM6pZdNwkaiZSuUXAeNT5BCBk4u5fHTxMcTDK



echo "======================================================"
echo "Create wallet"
cleos wallet create --file wallet.txt


echo "======================================================"
echo "Import wallet keys"
cleos \
    wallet import \
    --private-key 5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3

cleos \
    wallet import \
    --private-key 5HsVgxhxdL9gvgcAAyCZSWNgtLxAhGfEX2YU98w6QSkePoVvPNK

cleos \
    wallet import \
    --private-key 5K5UHY2LjHw2QQFJKCd2PdF7hxPJnknMfQLhxbEguJJttr1DFdp

cleos \
    wallet import \
    --private-key 5Je7woBXuxQBkpxit35SHZMap9SdKZLoeVBRKxntoMq2NuuN1rL


# we try it twice just in case the we get an "time exceeded" error
for value in {1, 2}
do

    echo "======================================================"
    echo "Create account user1"  # have no contract
    cleos \
        --url http://nodeos:8888 \
        create account eosio user1 \
        EOS5AvFzuUatd9ejnXKWWjjgjphGYRv3DSdpskkL3phC3q547kxCJ


    echo "======================================================"
    echo "Create account user2"  # will hold the samplecontract
    cleos \
        --url http://nodeos:8888 \
        create account eosio user2 \
        EOS5sRtLNDzsd9arp7J7qYSRRTcaLnRQFVkYtRuHn8tPeNS8D7DVM

    echo "======================================================"
    echo "Deploy contract simplecontract to user2"
    cleos \
        --url http://nodeos:8888 \
        set contract user2 . \
        /sample_contract/simplecontract.wasm /sample_contract/simplecontract.abi


    echo "======================================================"
    echo "Create account eosio.token"  # eosio.token core account
    cleos \
        --url http://nodeos:8888 \
        create account eosio eosio.token \
        EOS7dwjRjyyVPTg4UQQ3WozRhFLmspew8SP8BgbpTjrEPYs1c1rHV

    echo "======================================================"
    echo "Deploy eosio.token contract"
    cleos \
        --url http://nodeos:8888 \
        set contract eosio.token . \
        /sample_contract/eosio_token.wasm /sample_contract/eosio_token.abi

done
