from __future__ import annotations

import typing

import scalecodec
from bittensor.wallet import Wallet

from ...substrate.extrinsic import ExtrinsicResult
from ...substrate.pallets.author import DEFAULT_ERA, Era
from ..types import (
    HotKey,
    NetUid,
)
from ._base import Pallet
from ._types import StorageDoubleMap

if typing.TYPE_CHECKING:
    from .. import Subtensor


class SetCommitmentInfo(typing.TypedDict):
    fields: list[list[dict[str, bytes | dict[str, bytes | int]]]]


class GetCommitmentInfo(typing.TypedDict):
    fields: list[str | dict[str, str | dict[str, str | int]]]


class Registration(typing.TypedDict):
    block: int
    deposit: int
    info: GetCommitmentInfo


class Commitments(Pallet):
    def __init__(self, subtensor: Subtensor):
        super().__init__(subtensor)

        self.CommitmentOf = StorageDoubleMap[NetUid, HotKey, Registration](
            subtensor,
            "Commitments",
            "CommitmentOf",
            decode_value=_decode_registration,
        )

        self.RevealedCommitments = StorageDoubleMap[
            NetUid, HotKey, list[tuple[str, int]]
        ](
            subtensor,
            "Commitments",
            "RevealedCommitments",
        )

    async def set_commitment(
        self,
        netuid: int,
        info: SetCommitmentInfo,
        wallet: Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Sets the commitment info for a given hotkey on a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param info: The commitment info to set.
        :type info: SetCommitmentInfo
        :param wallet: The wallet associated with the account making this call.
        :type wallet:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "Commitments",
            "set_commitment",
            {
                "netuid": netuid,
                "info": info,
            },
            era=era,
            key=wallet.hotkey,
        )


def _decode_registration(registration: scalecodec.ScaleType) -> Registration:
    """
    Returns a decoded registration whose BigRaw fields hold their exact bytes as hex.

    scalecodec decodes BigRaw's byte vector to text when it is valid UTF-8, which loses
    the distinction between text such as "0xab" and the byte 0xab.
    """
    value: Registration = registration.value
    field_objects = (
        registration.value_object["info"].value_object["fields"].value_object
    )

    for field_object, field in zip(field_objects, value["info"]["fields"]):
        if not isinstance(field, dict) or "BigRaw" not in field:
            continue

        data = field_object.value_object[1].value_object
        if not isinstance(data, bytes | bytearray):
            raise TypeError(f"Unexpected BigRaw payload type {type(data).__name__}")

        field["BigRaw"] = f"0x{data.hex()}"

    return value
