import pytest

import eospyo


@pytest.fixture(scope="module")
def net():
    net = eospyo.Net(host="http://127.0.0.1:8888")
    yield net


@pytest.fixture
def auth():
    auth = eospyo.Authorization(actor="user2", permission="active")
    yield auth
