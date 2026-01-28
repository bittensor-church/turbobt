from __future__ import annotations

import enum
import ipaddress
import typing
from enum import IntEnum

import bittensor_wallet

from ...substrate.extrinsic import ExtrinsicResult
from ...substrate.pallets._types import StorageValue
from ...substrate.pallets.author import DEFAULT_ERA, Era
from ..types import (
    HotKey,
    NetUid,
    Uid,
)
from ._base import Pallet
from ._types import StorageDoubleMap

if typing.TYPE_CHECKING:
    from .. import Subtensor

PrivateKey: typing.TypeAlias = str
PublicKey: typing.TypeAlias = str


class CertificateAlgorithm(enum.IntEnum):
    ED25519 = 1
    """ EdDSA using ed25519 curve """


class NeuronCertificate(typing.TypedDict):
    algorithm: CertificateAlgorithm
    public_key: PublicKey


class NeuronCertificateKeypair(NeuronCertificate):
    private_key: PrivateKey


class AssociatedEvmAddress(typing.NamedTuple):
    h160_address: str
    last_block: int  # last block where ownership was proven


class ZippedWeights(typing.NamedTuple):
    uid: Uid
    weight: int


# I'm of a strong opinion that we should have a NewType for commit reveal version.
# However, since turbobt extensively uses primitive types, let's stick with it
# for the time being and see what comes out of BTSDK-14
# I'm also using an enum, because for some ungodly reason commit-reveal v3 is actually
# identified by version number 4, and if we start using numbers directly it's all gonna
# explode
class CommitRevealVersion(IntEnum):
    CRV3 = 4  # v3 is identified with 4 in SubtensorModule


class SubtensorModule(Pallet):
    def __init__(self, subtensor: Subtensor):
        super().__init__(subtensor)

        self.AssociatedEvmAddress = StorageDoubleMap[NetUid, Uid, AssociatedEvmAddress](
            subtensor,
            "SubtensorModule",
            "AssociatedEvmAddress",
        )
        self.NeuronCertificates = StorageDoubleMap[NetUid, HotKey, NeuronCertificate](
            subtensor,
            "SubtensorModule",
            "NeuronCertificates",
        )
        self.TimelockedWeightCommits = StorageDoubleMap[NetUid, int, None](
            subtensor,
            "SubtensorModule",
            "TimelockedWeightCommits",
        )
        self.TotalNetworks = StorageValue[int](
            subtensor,
            "SubtensorModule",
            "TotalNetworks",
        )
        self.Uids = StorageDoubleMap[NetUid, HotKey, Uid](
            subtensor,
            "SubtensorModule",
            "Uids",
        )
        self.Weights = StorageDoubleMap[NetUid, Uid, list[ZippedWeights]](
            subtensor,
            "SubtensorModule",
            "Weights",
        )

    async def add_stake(
        self,
        hotkey: str,
        netuid: int,
        amount_staked: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "add_stake",
            {
                "netuid": netuid,
                "hotkey": hotkey,
                "amount_staked": amount_staked,
            },
            key=wallet.coldkey,
            era=era,
        )

    async def burned_register(
        self,
        netuid: int,
        hotkey: str,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Registers a neuron on the Bittensor network by recycling TAO.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param hotkey: Hotkey to be registered to the network.
        :type hotkey: str
        :param wallet: The wallet associated with the neuron to be registered.
        :type wallet:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "burned_register",
            {
                "netuid": netuid,
                "hotkey": hotkey,
            },
            key=wallet.coldkey,
            era=era,
        )

    async def commit_crv3_weights(
        self,
        netuid: int,
        commit: bytes,
        reveal_round: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "commit_timelocked_mechanism_weights",
            {
                "netuid": netuid,
                "commit": f"0x{commit.hex()}",
                "reveal_round": reveal_round,
                "mecid": 0,  # backward-compatibility
                "commit_reveal_version": CommitRevealVersion.CRV3,
            },
            key=wallet.hotkey,
            era=era,
        )

    async def commit_timelocked_weights(
        self,
        netuid: int,
        commit: bytes,
        reveal_round: int,
        commit_reveal_version: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Commits timelocked weights for the default mechanism (mecid 0).

        This is a convenience wrapper over commit_timelocked_mechanism_weights that targets
        mechanism_id 0 for backward compatibility.

        :param netuid: Unique identifier of the subnet.
        :type netuid: int
        :param commit: Commitment bytes to submit (hex-encoded on chain).
        :type commit: bytes
        :param reveal_round: The round at which the corresponding reveal must occur.
        :type reveal_round: int
        :param commit_reveal_version: Commit-reveal version (e.g., 4 for CRV3). See commit_crv3_weights.
        :type commit_reveal_version: int
        :param wallet: Wallet whose hotkey signs the extrinsic.
        :type wallet: bittensor_wallet.Wallet
        :param era: Optional transaction era/mortality.
        :type era: Era | None
        :return: Asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "commit_timelocked_mechanism_weights",
            {
                "netuid": netuid,
                "commit": f"0x{commit.hex()}",
                "mecid": 0,  # backward compatibility
                "reveal_round": reveal_round,
                "commit_reveal_version": commit_reveal_version,
            },
            key=wallet.hotkey,
            era=era,
        )

    async def commit_timelocked_mechanism_weights(
        self,
        netuid: int,
        commit: bytes,
        mechanism_id: int,
        reveal_round: int,
        commit_reveal_version: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Commits timelocked weights for a mechanism (sub-subnet) using a commit-reveal scheme.

        :param netuid: Unique identifier of the subnet.
        :type netuid: int
        :param commit: Commitment bytes to submit (hex-encoded on chain).
        :type commit: bytes
        :param mechanism_id: Mechanism (mecid) identifier within the subnet.
        :type mechanism_id: int
        :param reveal_round: The round at which the corresponding reveal must occur.
        :type reveal_round: int
        :param commit_reveal_version: Commit-reveal version (e.g., 4 for CRV3).
        :type commit_reveal_version: int
        :param wallet: Wallet whose hotkey signs the extrinsic.
        :type wallet: bittensor_wallet.Wallet
        :param era: Optional transaction era/mortality.
        :type era: Era | None
        :return: Asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "commit_timelocked_mechanism_weights",
            {
                "netuid": netuid,
                "commit": f"0x{commit.hex()}",
                "mecid": mechanism_id,
                "reveal_round": reveal_round,
                "commit_reveal_version": commit_reveal_version,
            },
            key=wallet.hotkey,
            era=era,
        )

    async def register_network(
        self,
        hotkey: bittensor_wallet.Keypair,
        mechid: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "register_network",
            {
                "hotkey": hotkey,
                "mechid": mechid,
            },
            key=wallet.coldkey,
            era=era,
        )

    async def remove_stake(
        self,
        hotkey: str,
        netuid: int,
        amount_unstaked: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "remove_stake",
            {
                "amount_unstaked": amount_unstaked,
                "hotkey": hotkey,
                "netuid": netuid,
            },
            key=wallet.coldkey,
            era=era,
        )

    async def root_register(
        self,
        hotkey: str,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Registers a Neuron on the Bittensor's Root Subnet.

        :param hotkey: Hotkey to be registered to the network.
        :type hotkey: str
        :param wallet: The wallet associated with the neuron to be registered.
        :type wallet: bittensor_wallet.Wallet
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "root_register",
            {
                "hotkey": hotkey,
            },
            key=wallet.coldkey,
            era=era,
        )

    async def serve_axon(
        self,
        netuid: int,
        ip: str,
        port: int,
        wallet: bittensor_wallet.Wallet,
        protocol: int,
        version: int,
        placeholder1: int = 0,
        placeholder2: int = 0,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Submits an extrinsic to serve an Axon endpoint on the Bittensor network.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param ip: The IP address of the Axon endpoint.
        :type ip: str
        :param port: The port number for the Axon endpoint.
        :type port: int
        :param wallet: The wallet associated with the Axon service.
        :type wallet: bittensor_wallet.Wallet
        :param version: The Bittensor version identifier.
        :type version: int
        :param placeholder1: Placeholder for further extra params.
        :type placeholder1: int
        :param placeholder2: Placeholder for further extra params.
        :type placeholder2: int
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        ip_address = ipaddress.ip_address(ip)

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "serve_axon",
            {
                "ip_type": ip_address.version,
                "ip": int(ip_address),
                "netuid": netuid,
                "placeholder1": placeholder1,
                "placeholder2": placeholder2,
                "port": port,
                "protocol": protocol,
                "version": version,
            },
            key=wallet.hotkey,
            era=era,
        )

    async def serve_axon_tls(
        self,
        netuid: int,
        ip: str,
        port: int,
        certificate: bytes,
        wallet: bittensor_wallet.Wallet,
        protocol: int,
        version: int,
        placeholder1: int = 0,
        placeholder2: int = 0,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Submits an extrinsic to serve an Axon endpoint on the Bittensor network.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param ip: The IP address of the Axon endpoint.
        :type ip: str
        :param port: The port number for the Axon endpoint.
        :type port: int
        :param wallet: The wallet associated with the Axon service.
        :type wallet: bittensor_wallet.Wallet
        :param certificate: The certificate for securing the Axon endpoint.
        :type certificate: bytes
        :param protocol: Axon protocol. TCP, UDP, other.
        :type protocol: int
        :param version: The Bittensor version identifier.
        :type version: int
        :param placeholder1: Placeholder for further extra params.
        :type placeholder1: int
        :param placeholder2: Placeholder for further extra params.
        :type placeholder2: int
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        ip_address = ipaddress.ip_address(ip)

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "serve_axon_tls",
            {
                "certificate": certificate,
                "ip_type": ip_address.version,
                "ip": int(ip_address),
                "netuid": netuid,
                "placeholder1": placeholder1,
                "placeholder2": placeholder2,
                "port": port,
                "protocol": protocol,
                "version": version,
            },
            key=wallet.hotkey,
            era=era,
        )

    async def set_weights(
        self,
        netuid: int,
        dests: list[int],
        weights: list[int],
        version_key: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Sets weights for the default mechanism (mecid 0) on a subnet.

        This is a convenience wrapper over set_mechanism_weights that targets mechanism_id 0
        for backward compatibility.

        :param netuid: Unique identifier of the subnet.
        :type netuid: int
        :param dests: Destination neuron UIDs to weight.
        :type dests: list[int]
        :param weights: Weights corresponding to each destination UID.
        :type weights: list[int]
        :param version_key: Weights version key indicating encoding/version.
        :type version_key: int
        :param wallet: Wallet whose hotkey signs the extrinsic.
        :type wallet: bittensor_wallet.Wallet
        :param era: Optional transaction era/mortality.
        :type era: Era | None
        :return: Asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "set_mechanism_weights",
            {
                "netuid": netuid,
                "dests": dests,
                "mecid": 0,  # backward compatibility
                "weights": weights,
                "version_key": version_key,
            },
            key=wallet.hotkey,
            era=era,
        )

    async def set_mechanism_weights(
        self,
        netuid: int,
        dests: list[int],
        mechanism_id: int,
        weights: list[int],
        version_key: int,
        wallet: bittensor_wallet.Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Sets weights for the specified mechanism for specified neurons

        :param netuid: Unique identifier of the subnet.
        :type netuid: int
        :param dests: Destination neuron UIDs to weight.
        :type dests: list[int]
        :param mechanism_id: Mechanism (mecid) identifier within the subnet.
        :type mechanism_id: int
        :param weights: Weights corresponding to each destination UID.
        :type weights: list[int]
        :param version_key: Weights version key indicating encoding/version.
        :type version_key: int
        :param wallet: Wallet whose hotkey signs the extrinsic.
        :type wallet: bittensor_wallet.Wallet
        :param era: Optional transaction era/mortality.
        :type era: Era | None
        :return: Asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "SubtensorModule",
            "set_mechanism_weights",
            {
                "netuid": netuid,
                "dests": dests,
                "mecid": mechanism_id,
                "weights": weights,
                "version_key": version_key,
            },
            key=wallet.hotkey,
            era=era,
        )
