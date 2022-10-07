#include <eosio/eosio.hpp>
class [[eosio::contract]] test_contract : public eosio::contract {
  public:
      using eosio::contract::contract;
      [[eosio::action]] void hi( eosio::name user ) {
         print( "Hello, ", user);
      }
};