# start nodeos
nodeos -e -p eosio \
    --plugin eosio::producer_plugin \
    --plugin eosio::producer_api_plugin \
    --plugin eosio::chain_api_plugin \
    --plugin eosio::http_plugin \
    --plugin eosio::history_plugin \
    --plugin eosio::history_api_plugin \
    --filter-on="*" \
    --contracts-console \
    --http-validate-host=false \
    --http-server-address=0.0.0.0:8888 \
    --max-transaction-time 500 \
    --verbose-http-errors
