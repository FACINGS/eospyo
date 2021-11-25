import re

import pytest

import eospyo


aliases = [
    eospyo.EosMainnet,
    eospyo.KylinTestnet,
    eospyo.Jungle3Testnet,
    eospyo.TelosMainnet,
    eospyo.TelosTestnet,
    eospyo.ProtonMainnet,
    eospyo.ProtonTestnet,
    eospyo.UosMainnet,
    eospyo.FioMainnet,
    eospyo.WaxTestnet,
    eospyo.WaxMainnet,
]


@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize("alias", aliases)
def test_get_info_from_alias(alias):
    net = alias()
    info = net.get_info()
    assert isinstance(info, dict)
    assert "chain_id" in info
    patt = r"[a-f0-9]{64}"
    assert re.fullmatch(patt, info["chain_id"])
