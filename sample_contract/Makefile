CONTRACT=simplecontract

all: $(CONTRACT).wasm $(CONTRACT).abi

%.wasm: %.cpp %.hpp
	eosio-cpp -I. -o $@ $<

%.abi: %.cpp %.hpp
	eosio-abigen -contract=$(CONTRACT) --output=$@ $<

clean:
	rm -f $(CONTRACT).wasm $(CONTRACT).abi
