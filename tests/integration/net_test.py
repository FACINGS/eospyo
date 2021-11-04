import re

import eospyo


def test_waxtestnet():
    net = eospyo.WaxTestnet()
    info = net.get_info()
    assert isinstance(info, tuple)
    assert hasattr(info, "chain_id")
    patt = r"[a-f0-9]{64}"
    assert re.fullmatch(patt, info.chain_id)


def test_waxmainnet():
    net = eospyo.WaxMainnet()
    info = net.get_info()
    assert isinstance(info, tuple)
    assert hasattr(info, "chain_id")
    patt = r"[a-f0-9]{64}"
    assert re.fullmatch(patt, info.chain_id)
