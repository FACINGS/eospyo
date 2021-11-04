#include "simplecontract.hpp"

ACTION simplecontract::sendmsg(name from, string message) {
    require_auth(from);

    // Init the _message table
    messages_table _messages(get_self(), get_self().value);

    // Find the record from _messages table
    auto msg_itr = _messages.find(from.value);
    if (msg_itr == _messages.end()) {
        // Create a message record if it does not exist
        _messages.emplace(from, [&](auto& msg) {
            msg.user = from;
            msg.text = message;
        });
        print("New msg. Name: ", name{from},"; Message: ", name{message});
    } else {
        // Modify a message record if it exists
        _messages.modify(msg_itr, from, [&](auto& msg) {
            msg.text = message;
        });
    }
}

ACTION simplecontract::clear() {
    require_auth(get_self());

    messages_table _messages(get_self(), get_self().value);

    // Delete all records in _messages table
    auto msg_itr = _messages.begin();
    while (msg_itr != _messages.end()) {
        msg_itr = _messages.erase(msg_itr);
    }
}

ACTION simplecontract::testname(name var) {}
ACTION simplecontract::teststring(string var) {}
ACTION simplecontract::tinteight(int8_t var) {}
ACTION simplecontract::tuinteight(uint8_t var) {}
ACTION simplecontract::tuintsixteen(uint16_t var) {}
ACTION simplecontract::tuintthirtwo(uint32_t var) {}
ACTION simplecontract::tuintsixfour(uint64_t var) {}

EOSIO_DISPATCH(simplecontract, (sendmsg)(clear))
