"""type tests."""

import datetime as dt
from pathlib import Path

import pydantic
import pytest

import eospyo
from eospyo import types

values = [
    (types.Bool, True, b"\x01"),
    (types.Bool, False, b"\x00"),
    (types.Int8, -128, b"\x80"),
    (types.Int8, -127, b"\x81"),
    (types.Int8, -1, b"\xFF"),
    (types.Int8, 0, b"\x00"),
    (types.Int8, 1, b"\x01"),
    (types.Int8, 127, b"\x7F"),
    (types.Uint8, 0, b"\x00"),
    (types.Uint8, 1, b"\x01"),
    (types.Uint8, 254, b"\xFE"),
    (types.Uint8, 255, b"\xFF"),
    (types.Uint16, 0, b"\x00\x00"),
    (types.Uint16, 1, b"\x01\x00"),
    (types.Uint16, 2 ** 16 - 2, b"\xFE\xFF"),
    (types.Uint16, 2 ** 16 - 1, b"\xFF\xFF"),
    (types.Uint32, 0, b"\x00\x00\x00\x00"),
    (types.Uint32, 1, b"\x01\x00\x00\x00"),
    (types.Uint32, 10800, b"0*\x00\x00"),
    (types.Uint32, 10800, b"\x30\x2a\x00\x00"),
    (types.Uint32, 123456, b"@\xe2\x01\x00"),
    (types.Uint32, 2 ** 32 - 2, b"\xFE\xFF\xFF\xFF"),
    (types.Uint32, 2 ** 32 - 1, b"\xFF\xFF\xFF\xFF"),
    (types.Uint64, 0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.Uint64, 1, b"\x01\x00\x00\x00\x00\x00\x00\x00"),
    (types.Uint64, 2 ** 64 - 2, b"\xFE\xFF\xFF\xFF\xFF\xFF\xFF\xFF"),
    (types.Uint64, 2 ** 64 - 1, b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"),
    (types.Varuint32, 0, b"\x00"),
    (types.Varuint32, 1, b"\x01"),
    (types.Varuint32, 3, b"\x03"),
    (types.Varuint32, 2 ** 8 - 1, b"\xFF\x01"),
    (types.Varuint32, 2 ** 8, b"\x80\x02"),
    (types.Varuint32, 2 ** 32 - 1, b"\xFF\xFF\xFF\xFF\x0F"),
    (types.Varuint32, 2 ** 32, b"\x80\x80\x80\x80\x10"),
    (types.Varuint32, 20989371979, b"\xcb\xcc\xc1\x98N"),
    (types.Name, "a", b"\x00\x00\x00\x00\x00\x00\x000"),
    (types.Name, "a.", b"\x00\x00\x00\x00\x00\x00\x000"),
    (types.Name, "b", b"\x00\x00\x00\x00\x00\x00\x008"),
    (types.Name, "zzzzzzzzzzzzj", b"\xff\xff\xff\xff\xff\xff\xff\xff"),
    (types.Name, "kacjndfvdfa", b"\x00\xccJ{\xa5\xf9\x90\x81"),
    (types.Name, "user2", b"\x00\x00\x00\x00\x00q\x15\xd6"),
    (types.Name, "", b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.String, "a", b"\x01a"),
    (types.String, "A", b"\x01A"),
    (types.String, "kcjansdcd", b"\tkcjansdcd"),
    (types.String, "", b"\x00"),
    (types.UnixTimestamp, dt.datetime(1970, 1, 1, 0, 0), b"\x00\x00\x00\x00"),
    (
        types.UnixTimestamp,
        dt.datetime(2040, 12, 31, 23, 59),
        b"\x44\x03\x8D\x85",
    ),
    (
        types.UnixTimestamp,
        dt.datetime(2040, 12, 31, 23, 59, 0),
        b"\x44\x03\x8D\x85",
    ),
    (
        types.UnixTimestamp,
        dt.datetime(2021, 8, 26, 14, 1, 47),
        b"\xCB\x9E\x27\x61",
    ),
    (
        types.UnixTimestamp,
        dt.datetime(2021, 8, 26, 14, 1, 47, 184549),
        b"\xCB\x9E\x27\x61",
    ),
    # minumum amount of characters
    (types.Symbol, "0,W", b"\x00W\x00\x00\x00\x00\x00\x00"),
    # maximum amount of characters
    (types.Symbol, "0,WAXXXXX", b"\x00WAXXXXX"),
    # 1 precision
    (types.Symbol, "1,WAX", b"\x01WAX\x00\x00\x00\x00"),
    # max precision
    (types.Symbol, "16,WAX", b"\x10WAX\x00\x00\x00\x00"),
    (
        types.Asset,
        "99.9 WAX",
        b"\xe7\x03\x00\x00\x00\x00\x00\x00\x01WAX\x00\x00\x00\x00",
    ),
    (
        types.Asset,
        "99 WAX",
        b"c\x00\x00\x00\x00\x00\x00\x00\x00WAX\x00\x00\x00\x00",
    ),
    (
        types.Wasm,
        "test_contract/test_contract.wasm",
        "test_contract/bin_files/wasm_pass_bytes.bin",
    ),
    (
        types.Abi,
        "test_contract/test_contract.abi",
        "test_contract/bin_files/abi_pass_bytes.bin",
    ),
]


@pytest.mark.parametrize("class_,input_,expected_output", values)
def test_type_bytes(class_, input_, expected_output):
    uses_file = {
        types.Abi,
        types.Wasm,
    }
    if class_ in uses_file:
        filename = str(Path().resolve()) + "/" + expected_output
        with open(filename, "rb") as f:
            content = f.read()
        print(repr(content))
        expected_output = content

    instance = class_(input_)
    output = bytes(instance)
    print("bytes:\n" + str(output))
    assert output == expected_output


@pytest.mark.parametrize("class_,input_,expected_output", values)
def test_bytes_to_type(class_, input_, expected_output):
    uses_file = {
        types.Abi,
        types.Wasm,
    }
    if class_ in uses_file:
        filename = Path().resolve() / expected_output
        with open(filename, "rb") as f:
            content = f.read()
        expected_output = content

    instance = class_(input_)
    bytes_ = bytes(instance)
    print(f"{instance=}; {bytes_=}")
    new_instance = class_.from_bytes(bytes_)
    assert new_instance == instance


@pytest.mark.parametrize("class_,input_,expected_output", values)
def test_size(class_, input_, expected_output):
    has_len = {
        types.Varuint32,
        types.String,
    }
    if class_ in has_len:
        instance = class_(input_)
        bytes_ = bytes(instance)
        assert len(instance) == len(bytes_)


test_serialization = [
    ("name", "testname", "hrforxogkfjv"),
    ("name", "testname", ""),
    ("string", "teststring", "hrforxogkfjv"),
    ("string", "teststring", "Lorem Ipsum " * 10),
    (
        "string",
        "teststring",
        "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]"
        + "^_`abcdefghijklmnopqrstuvwxyz{|}~ ",
    ),
    ("string", "teststring", ""),
    ("int8", "tinteight", -128),
    ("int8", "tinteight", -127),
    ("int8", "tinteight", 0),
    ("int8", "tinteight", 1),
    ("int8", "tinteight", 127),
    ("uint8", "tuinteight", 0),
    ("uint8", "tuinteight", 1),
    ("uint8", "tuinteight", 254),
    ("uint8", "tuinteight", 255),
    ("uint16", "tuintsixteen", 0),
    ("uint16", "tuintsixteen", 1),
    ("uint16", "tuintsixteen", 2),
    ("uint16", "tuintsixteen", 2 ** 16 - 2),
    ("uint16", "tuintsixteen", 2 ** 16 - 1),
    ("uint32", "tuintthirtwo", 0),
    ("uint32", "tuintthirtwo", 1),
    ("uint32", "tuintthirtwo", 10800),
    ("uint32", "tuintthirtwo", 10800),
    ("uint32", "tuintthirtwo", 123456),
    ("uint32", "tuintthirtwo", 2 ** 32 - 2),
    ("uint32", "tuintthirtwo", 2 ** 32 - 1),
    ("uint64", "tuintsixfour", 0),
    ("uint64", "tuintsixfour", 1),
    ("uint64", "tuintsixfour", 2 ** 64 - 2),
    ("uint64", "tuintsixfour", 2 ** 64 - 1),
]


@pytest.mark.parametrize("type_,action, value", test_serialization)
def test_abi_vs_eospyo_serialization(net, type_, action, value):
    data_as_dict = dict(name="var", value=value, type=type_)
    data = eospyo.Data.parse_obj(data_as_dict)
    eospyo_data_bytes = bytes(data)

    nodeos_action_bytes = net.abi_json_to_bin(
        account_name="user2",
        action=action,
        json={"var": value},
    )
    assert eospyo_data_bytes == nodeos_action_bytes


error_values = [
    (types.Int8, -129),
    (types.Int8, 128),
    (types.Uint8, -1),
    (types.Uint8, 256),
    (types.Uint16, -1),
    (types.Uint16, 2 ** 16),
    (types.Uint32, -1),
    (types.Uint32, 2 ** 32),
    (types.Uint64, -1),
    (types.Uint64, 2 ** 64),
    # (types.Name, ""),
    (types.Name, "A"),
    (types.Name, "z" * 14),
    (types.Name, "á"),
    (types.Name, "."),
    (types.Name, "...."),
    (types.Name, "zzzzzzzzzzzzz"),
    (types.Name, "aaaaaaaaaaaaz"),
    (types.Name, "............z"),
    (types.Varuint32, -1),
    (types.Varuint32, 20989371980),
    # utf 2 byte char
    (types.String, "µ"),
    (types.String, "aµ"),
    (types.String, "µa"),
    (types.String, "aµa"),
    # utf 3 byte char
    (types.String, "ࢠ"),
    (types.String, "aࢠ"),
    (types.String, "ࢠa"),
    # utf 4 byte char
    (types.String, "𒀀"),
    (types.String, "a𒀀"),
    (types.String, "𒀀a"),
    # additional utf 4 byte char
    (types.String, "🤎"),
    (types.String, "a🤎"),
    (types.String, "🤎a"),
    (types.Symbol, "0,WAXXXXXX"),
    (types.Symbol, "0,"),
    (types.Symbol, "0, "),
    (types.Symbol, ","),
    (types.Symbol, "17,WAX"),
    (types.Symbol, "-1,WAX"),
    (types.Asset, "1WAX"),
    (types.Asset, "1 1 WAX"),
    (types.Asset, "WAX"),
    (types.Asset, "-1 WAX"),
    (types.Asset, str(2 ** 64) + " WAX"),
    (types.Asset, "1 WAXXXXXX"),
    (types.Asset, "99 "),
    (types.Asset, "99"),
    (types.Asset, "99. WAXXXXXX"),
    (types.Asset, "99."),
    (types.Abi, "test_contract/invalid_test_contract.abi"),
    (types.Abi, "test_contract/extra_field_test_contract.abi"),
    (types.Wasm, "test_contract/invalid_test_contract - 2.wasm"),
    (types.Wasm, "test_contract/odd_number_test_contract.wasm"),
]


@pytest.mark.parametrize("class_,input_", error_values)
def test_type_validation_errors(class_, input_):
    with pytest.raises(pydantic.ValidationError):
        class_(input_)


array_values = [
    (
        types.Int8,
        [-128, -127, 126, 127],
        b"\x04\x80\x81\x7E\x7F",
    ),
    (
        types.Varuint32,
        [0, 2 ** 8, 2 ** 16, 2 ** 4],
        b"\x04\x00\x80\x02\x80\x80\x04\x10",
    ),
]


@pytest.mark.parametrize("type_,input_,expected_output", array_values)
def test_array_to_bytes(type_, input_, expected_output):
    array = types.Array(type_=type_, values=input_)
    output = bytes(array)
    assert output == expected_output


@pytest.mark.parametrize("type_,input_,expected_output", array_values)
def test_bytes_to_array(type_, input_, expected_output):
    array = types.Array(type_=type_, values=input_)
    bytes_ = bytes(array)
    print(f"{array=}; {bytes_=}")
    array_from_bytes = types.Array.from_bytes(bytes_, type_)
    assert array_from_bytes == array, f"{array=}; {array_from_bytes=}"


@pytest.mark.parametrize("class_,input_", error_values)
def test_array_validation_errors(class_, input_):
    with pytest.raises(pydantic.ValidationError):
        types.Array(type_=class_, values=[input_])


def test_array_initialized_with_list_and_tuples_returns_the_same_result():
    arr1 = types.Array(values=[1, 2, 3], type_=types.Int8)
    arr2 = types.Array(values=(1, 2, 3), type_=types.Int8)
    assert hash(arr1) == hash(arr2)


def test_array_initialized_with_list_and_range_returns_the_same_result():
    arr1 = types.Array(values=[1, 2, 3], type_=types.Int8)
    arr2 = types.Array(values=range(1, 4), type_=types.Int8)
    assert hash(arr1) == hash(arr2)


def test_array_initialized_with_list_and_string_returns_the_same_result():
    arr1 = types.Array(values=["a", "b", "c"], type_=types.Name)
    arr2 = types.Array(values="abc", type_=types.Name)
    assert hash(arr1) == hash(arr2)


def test_array_elements_are_immutable_directly():
    arr = types.Array(values=[1, 2, 3], type_=types.Int8)
    with pytest.raises(TypeError):
        arr[1] = 2


def test_array_elements_are_immutable_when_try_to_mutate_value():
    arr = types.Array(values=[1, 2, 3], type_=types.Int8)
    with pytest.raises(TypeError):
        arr.values[1] = 2


def test_eosio_type_cannot_be_instantiated():
    with pytest.raises(TypeError):
        types.EosioType()


def test_array_can_be_sliced_1():
    arr_full = types.Array(values=range(10), type_=types.Int8)
    arr_slice = types.Array(values=range(10)[1:4], type_=types.Int8)
    assert arr_full[1:4] == arr_slice


def test_array_can_be_sliced_2():
    arr_full = types.Array(values=range(10), type_=types.Int8)
    arr_slice = types.Array(values=range(10)[8:3:-2], type_=types.Int8)
    assert arr_full[8:3:-2] == arr_slice
