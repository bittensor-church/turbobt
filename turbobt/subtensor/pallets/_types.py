from __future__ import annotations

import typing

import scalecodec

from ...substrate._hashers import HASHERS
from ...substrate.pallets.state import StorageChangeSet
from ..types import HotKey

if typing.TYPE_CHECKING:
    from ...subtensor import Subtensor


K1 = typing.TypeVar("K1")
K2 = typing.TypeVar("K2")
V = typing.TypeVar("V")


class StorageDoubleMap(typing.Generic[K1, K2, V]):
    def __init__(self, subtensor: Subtensor, module: str, storage: str):
        self.subtensor = subtensor
        self.module = module
        self.storage = storage

    async def get(self, key1: K1, key2: K2, block_hash=None) -> V:
        return await self.subtensor.state.getStorage(
            f"{self.module}.{self.storage}",
            key1,
            key2,
            block_hash=block_hash,
        )

    async def fetch(
        self,
        *args,
        block_hash: str = None,
    ) -> list[tuple[tuple[K1, K2], V]]:
        await self.subtensor._init_runtime()

        pallet = self.subtensor._metadata.get_metadata_pallet(self.module)
        storage_function = pallet.get_storage_function(self.storage)

        prefix = self.subtensor.state._storage_key(
            pallet,
            storage_function,
            args,
        )

        page_size = 1000
        keys = []
        start_key = ""
        while True:
            page = await self.subtensor.state.getKeysPaged(
                prefix,
                page_size,
                start_key=start_key,
                block_hash=block_hash,
            )
            keys.extend(page)
            if len(page) < page_size:
                break
            start_key = page[-1]
        results = await self.subtensor.state.queryStorageAt(
            keys,
            block_hash=block_hash,
        )

        return self._decode(results)

    def _decode(
        self,
        results: list[StorageChangeSet],
    ) -> list[tuple[tuple[K1, K2], V]]:
        pallet = self.subtensor._metadata.get_metadata_pallet(self.module)
        storage_function = pallet.get_storage_function(self.storage)

        param_types = storage_function.get_params_type_string()
        param_hashers = storage_function.get_param_hashers()

        key_type_string = []

        for param_hasher, param_type in zip(param_hashers, param_types):
            try:
                hasher = HASHERS[param_hasher]
            except KeyError:
                raise NotImplementedError(param_hasher)

            key_type_string.append(f"[u8; {hasher.hash_length}]")
            key_type_string.append(param_type)

        key_type = self.subtensor._registry.create_scale_object(
            f"({', '.join(key_type_string)})",
        )
        value_type = self.subtensor._registry.create_scale_object(
            storage_function.get_value_type_string(),
        )

        prefix = self.subtensor.state._storage_key(
            pallet,
            storage_function,
            [],
        )

        results = (
            (
                bytearray.fromhex(key.removeprefix(prefix)),
                bytearray.fromhex(value[2:]),
            )
            for result in results
            for key, value in result["changes"]
        )
        results = (
            (
                key_type.decode(
                    scalecodec.ScaleBytes(key),
                ),
                value_type.decode(
                    scalecodec.ScaleBytes(value),
                ),
            )
            for key, value in results
        )
        results = (
            (
                # remove key hashes
                (
                    key[1],
                    key[3],
                ),
                value,
            )
            for key, value in results
        )

        # decode K1 as HotKey
        if self.__orig_class__.__args__[0] is HotKey:
            results = (
                (
                    (
                        scalecodec.utils.ss58.ss58_encode(keys[0]),
                        keys[1],
                    ),
                    value,
                )
                for keys, value in results
            )

        # decode K2 as HotKey
        if self.__orig_class__.__args__[1] is HotKey:
            results = (
                (
                    (
                        keys[0],
                        scalecodec.utils.ss58.ss58_encode(keys[1]),
                    ),
                    value,
                )
                for keys, value in results
            )

        return list(results)
