import typing

import scalecodec

from .._hashers import (
    HASHERS,
    xxh128,
)
from ._base import Pallet


class RuntimeVersion(typing.TypedDict):
    specVersion: int
    transactionVersion: int
    # ...


class StorageChangeSet(typing.TypedDict):
    block: str
    changes: list[tuple[str, str]]


class State(Pallet):
    async def call(
        self,
        method: str,
        data: str,
        block_hash: str | None = None,
    ) -> int | bytearray | dict:
        """
        Perform a call to a builtin on the chain.

        :param method: The name of the built-in function you want to call
        :type method: str
        :param data: The input data to be passed to the built-in function as bytes.
        :type data: str
        :param block_hash: The hash of a specific block in the chain.
        :type block_hash: str
        :return: The output of the call to the built-in function.
        :rtype: int | bytearray | dict
        """
        return await self.substrate.rpc(
            method="state_call",
            params={
                "name": method,
                "bytes": data,
                "hash": block_hash,
            },
        )

    async def getMetadata(
        self,
        block_hash: str | None = None,
    ) -> scalecodec.ScaleType:
        """
        Returns the runtime metadata.

        :param block_hash: The block hash to retrieve runtime metadata.
        :type block_hash:
        :return: Runtime Metadata.
        :rtype: ScaleType
        """

        await self.substrate._init_runtime()

        response = await self.substrate.rpc(
            method="state_getMetadata",
            params={
                "hash": block_hash,
            },
        )

        metadata = self.substrate._registry.create_scale_object(
            "MetadataVersioned",
            data=scalecodec.ScaleBytes(response),
        )
        metadata.decode()

        return metadata  # .value?

    async def getRuntimeVersion(self, block_hash=None) -> RuntimeVersion:
        """
        Get the runtime version.

        :param block_hash: The hash of a specific block in the chain. If not provided, the request will return the runtime version from the latest block.
        :type block_hash:
        :return: Runtime Version.
        :rtype: RuntimeVersion
        """

        return await self.substrate.rpc(
            method="state_getRuntimeVersion",
            params={
                "hash": block_hash,
            },
        )

    async def getKeys(
        self,
        prefix: str,
        block_hash=None,
    ) -> list:
        """
        Returns the keys with prefix from a child storage.

        :param prefix: The Storage Key prefix.
        :type prefix: str
        :param block_hash: The hash of a specific block in the chain. Providing this parameter ensures that the keys are queried at the state corresponding to that block. If not provided, the request will use the latest block.
        :type block_hash:
        :return: A list of keys.
        :rtype: list
        """

        await self.substrate._init_runtime()

        return await self.substrate.rpc(
            method="state_getKeys",
            params={
                "prefix": prefix,
                "hash": block_hash,
            },
        )

    async def getKeysPaged(
        self,
        prefix: str,
        count: int,
        start_key: str | None = "",
        block_hash=None,
    ) -> list:
        """
        Returns the keys with prefix from a child storage with pagination support.

        :param prefix: The Storage Key prefix.
        :type key: str
        :param count: The number of results to include per page.
        :type count: int
        :param start_key: This parameter is used for pagination, indicating the starting key to fetch results from. If not provided, the request will start from the beginning.
        :type start_key:
        :param block_hash: The hash of a specific block in the chain. Providing this parameter ensures that the keys are queried at the state corresponding to that block. If not provided, the request will use the latest block.
        :type block_hash:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: list
        """

        await self.substrate._init_runtime()

        return await self.substrate.rpc(
            method="state_getKeysPaged",
            params={
                "prefix": prefix,
                "count": count,
                "startKey": start_key,
                "hash": block_hash,
            },
        )

    async def getStorage(
        self,
        key: str,
        *params,
        block_hash=None,
    ):
        """
        Returns a child storage entry at a specific block state.

        :param key: The storage name.
        :type key: str
        :param params: Parts of Storage Key for which you want to retrieve the storage data.
        :type params:
        :param block_hash: The hash of a specific block in the chain.
        :type block_hash:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: Any | None
        """

        await self.substrate._init_runtime()

        pallet, storage_function = key.split(".", 1)
        pallet = self.substrate._metadata.get_metadata_pallet(pallet)
        storage_function = pallet.get_storage_function(storage_function)

        key = self._storage_key(
            pallet,
            storage_function,
            params,
        )

        result = await self.substrate.rpc(
            method="state_getStorage",
            params={
                "key": key,
                "hash": block_hash,
            },
        )

        if result is None:
            return

        res = self.substrate._registry.create_scale_object(
            storage_function.get_value_type_string(),  # metadata=metadata
        )

        return res.decode(
            scalecodec.ScaleBytes(result),
        )

    async def queryStorageAt(
        self,
        keys: list[str],
        block_hash=None,
    ) -> list[StorageChangeSet]:
        """
        Query storage entries (by key) starting at block hash given as the second parameter.

        :param keys: An array representing the key or keys for which you want to retrieve storage entries.
        :type keys: list[str]
        :param block_hash: The hash of a specific block in the chain.
        :type block_hash:
        :return: An array representing the set of changes to the storage entries starting from the specified block hash. Each element of the array corresponds to a storage entry change.
        :rtype: list[StorageChangeSet]
        """

        await self.substrate._init_runtime()

        return await self.substrate.rpc(
            method="state_queryStorageAt",
            params={
                "keys": keys,
                "hash": block_hash,
            },
        )

    async def queryStorage(
        self,
        keys: list[str],
        from_block_hash: str,
        to_block_hash: str | None = None,
    ) -> list[StorageChangeSet]:
        """
        Query storage entries (by key) across a block range.

        :param keys: An array representing the key or keys for which you want to
            retrieve storage entries.
        :type keys: list[str]
        :param from_block_hash: The hash of the block where the historical query
            should start.
        :type from_block_hash: str
        :param to_block_hash: The hash of the block where the historical query
            should stop. If not provided, the node default is used.
        :type to_block_hash: str | None
        :return: An array representing the set of changes to the storage entries
            across the specified block range.
        :rtype: list[StorageChangeSet]
        """

        await self.substrate._init_runtime()

        return await self.substrate.rpc(
            method="state_queryStorage",
            params={
                "keys": keys,
                "from_block": from_block_hash,
                "to_block": to_block_hash,
            },
        )

    async def subscribeStorage(
        self,
        key: str,
        *params,
    ) -> str:
        await self.substrate._init_runtime()

        pallet, storage_function = key.split(".", 1)
        pallet = self.substrate._metadata.get_metadata_pallet(pallet)
        storage_function = pallet.get_storage_function(storage_function)

        key = self._storage_key(
            pallet,
            storage_function,
            params,
        )

        subscription_id_raw = await self.substrate.rpc(
            method="state_subscribeStorage",
            params={
                "keys": [key],
            },
        )
        subscription_id = f"0x{subscription_id_raw.hex()}"

        return subscription_id

    async def unsubscribeStorage(self, subscription_id: str) -> bool:
        await self.substrate._init_runtime()

        return await self.substrate.rpc(
            method="state_unsubscribeStorage",
            params=[
                subscription_id,
            ],
        )

    def _storage_key(self, pallet, storage_function, params):
        param_types = storage_function.get_params_type_string()
        param_hashers = storage_function.get_param_hashers()

        storage_hash = xxh128(pallet.value["storage"]["prefix"].encode()) + xxh128(
            storage_function.value["name"].encode()
        )

        if param_types:
            params = tuple(
                self.substrate._registry.create_scale_object(
                    param_type,
                ).encode(
                    param_value,
                )
                for param_value, param_type in zip(params, param_types)
            )

            for param_value, param_hash in zip(params, param_hashers):
                try:
                    hasher = HASHERS[param_hash]
                except KeyError:
                    raise NotImplementedError(param_hash)

                storage_hash += hasher.function(param_value.data)

        return f"0x{storage_hash.hex()}"
