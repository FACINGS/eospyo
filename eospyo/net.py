"""
Blockchain network main class and its derivatives.

Nodeos api reference:
https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index
"""

import typing
from urllib.parse import urljoin

import httpx
import pydantic

from eospyo import exc


class Net(pydantic.BaseModel):
    """
    The net hold the connection information with the blockchain network api.
    """  # NOQA: D200

    host: pydantic.AnyHttpUrl

    def _request(
        self,
        *,
        endpoint: str,
        payload: typing.Optional[dict] = dict(),
        verb: str = "POST",
    ):
        url = urljoin(self.host, endpoint)

        try:
            resp = httpx.post(url, json=payload)
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.WriteError,
        ) as e:
            raise exc.ConnectionError(
                response=None, url=url, payload=payload, error=e
            )

        if resp.status_code > 299 and resp.status_code != 500:
            raise exc.ConnectionError(
                response=resp, url=url, payload=payload, error=None
            )

        return resp.json()

    def abi_bin_to_json(
        self, *, account_name: str, action: str, bytes: dict
    ) -> dict:
        endpoint = "/v1/chain/abi_bin_to_json"
        payload = dict(code=account_name, action=action, binargs=bytes.hex())
        data = self._request(endpoint=endpoint, payload=payload)
        return data["args"]

    def abi_json_to_bin(
        self, *, account_name: str, action: str, json: dict
    ) -> bytes:
        """
        Return a dict containing the serialized action data.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/abi_json_to_bin
        """
        endpoint = "/v1/chain/abi_json_to_bin"
        payload = dict(code=account_name, action=action, args=json)
        data = self._request(endpoint=endpoint, payload=payload)
        if "binargs" not in data:
            return data
        hex_ = data["binargs"]
        bytes_ = bytes.fromhex(hex_)
        return bytes_

    def get_info(self):
        endpoint = "/v1/chain/get_info"
        data = self._request(endpoint=endpoint)
        return data

    def get_account(self, *, account_name: str):
        """
        Return an account information.

        If no account is found, then raises an connection error
        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_account
        """
        endpoint = "/v1/chain/get_account"
        payload = dict(account_name=account_name)
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def get_abi(self, *, account_name: str):
        """
        Retrieve the ABI for a contract based on its account name.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_abi
        """
        endpoint = "/v1/chain/get_abi"
        payload = dict(account_name=account_name)
        data = self._request(endpoint=endpoint, payload=payload)
        if len(data) == 1:
            return None
        return data

    def get_block(self, *, block_num_or_id: str):
        """
        Return various details about a specific block on the blockchain.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_block
        """
        endpoint = "/v1/chain/get_block"
        payload = dict(block_num_or_id=block_num_or_id)
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def get_block_info(self, *, block_num: str):
        """
        Return a fixed-size smaller subset of the block data.

        Similar to get_block
        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_block_info
        """
        endpoint = "/v1/chain/get_block_info"
        payload = dict(block_num=block_num)
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def push_transaction(
        self,
        *,
        transaction: object,
        compression: bool = False,
        packed_context_free_data: str = "",
    ):
        """
        Send a transaction to the blockchain.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/push_transaction
        """
        endpoint = "/v1/chain/push_transaction"
        payload = dict(
            signatures=transaction.signatures,
            compression=compression,
            packed_context_free_data=packed_context_free_data,
            packed_trx=transaction.pack(),
        )
        data = self._request(endpoint=endpoint, payload=payload)
        return data


class WaxTestnet(Net):
    host: pydantic.HttpUrl = "https://testnet.waxsweden.org/"


class WaxMainnet(Net):
    host: pydantic.HttpUrl = "https://facings.waxpub.net"


class Local(Net):
    host: pydantic.HttpUrl = "http://127.0.0.1:8888"


__all__ = ["Net", "WaxTestnet", "WaxMainnet", "Local"]
