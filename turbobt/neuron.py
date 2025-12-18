from __future__ import annotations

import dataclasses
import enum
import ipaddress
import typing

import bittensor_wallet

from turbobt.block import get_ctx_block_hash

from .substrate._scalecodec import u16_proportion_to_float

if typing.TYPE_CHECKING:
    from turbobt.subtensor.pallets.subtensor_module import NeuronCertificate

    from .subnet import Subnet


class AxonProtocolEnum(enum.IntEnum):
    # https://github.com/opentensor/subtensor/blob/a1bf521444a80c86c37f1573af2e8860700c0b79/pallets/subtensor/src/subnets/serving.rs#L26

    TCP = 0
    UDP = 1
    HTTP = 4  # ?


@dataclasses.dataclass
class AxonInfo:
    # block: int
    # version: int
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address
    port: int
    # ip_type: int
    protocol: AxonProtocolEnum
    # placeholder1: int
    # placeholder2: int

    @classmethod
    def from_dict(cls, axon_info) -> AxonInfo:
        return cls(
            # block=axon_info["block"],
            # version=axon_info["version"],
            ip=ipaddress.ip_address(axon_info["ip"]),
            port=axon_info["port"],
            # ip_type=axon_info["ip_type"],
            protocol=axon_info["protocol"],
            # placeholder1=axon_info["placeholder1"],
            # placeholder2=axon_info["placeholder2"],
        )


@dataclasses.dataclass
class PrometheusInfo:
    # block: int
    # version: int
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address
    port: int
    # ip_type: int

    @classmethod
    def from_dict(cls, prometheus_info) -> PrometheusInfo:
        return cls(
            # block=prometheus_info["block"],
            # version=prometheus_info["version"],
            ip=ipaddress.ip_address(prometheus_info["ip"]),
            port=prometheus_info["port"],
            # ip_type=prometheus_info["ip_type"],
        )


@dataclasses.dataclass(
    kw_only=True,
    order=True,
)
class Neuron:
    subnet: Subnet
    # netuid: int
    uid: int
    coldkey: str
    hotkey: str
    active: bool = dataclasses.field(compare=False, repr=False)
    axon_info: AxonInfo = dataclasses.field(compare=False, repr=False)
    prometheus_info: PrometheusInfo = dataclasses.field(compare=False, repr=False)
    # stake: dict[str, float] # TODO?
    stake: float  # TODO Balance  # total stake (alpha)
    rank: float
    emission: float
    incentive: float
    consensus: float
    trust: float
    validator_trust: float
    dividends: float
    last_update: int
    validator_permit: bool
    pruning_score: int

    @classmethod
    def from_dict(cls, neuron: dict, *, subnet: Subnet):
        return cls(
            subnet=subnet,
            # netuid=neuron["netuid"],
            active=neuron["active"],
            axon_info=AxonInfo.from_dict(neuron["axon_info"]),
            coldkey=neuron["coldkey"],
            consensus=u16_proportion_to_float(neuron["consensus"]),
            dividends=u16_proportion_to_float(neuron["dividends"]),
            emission=neuron["emission"] / 1e9,  # TODO
            hotkey=neuron["hotkey"],
            incentive=u16_proportion_to_float(neuron["incentive"]),
            last_update=neuron["last_update"],
            prometheus_info=PrometheusInfo.from_dict(neuron["prometheus_info"]),
            pruning_score=neuron["pruning_score"],
            rank=u16_proportion_to_float(neuron["rank"]),
            stake=next(value / 1_000_000_000 for value in neuron["stake"].values()),
            trust=u16_proportion_to_float(neuron["trust"]),
            uid=neuron["uid"],
            validator_permit=neuron["validator_permit"],
            validator_trust=u16_proportion_to_float(neuron["validator_trust"]),
        )

    def __hash__(self):
        return hash(self.hotkey or self.uid)


@dataclasses.dataclass
class NeuronReference:
    subnet: Subnet
    uid: int | None = None
    hotkey: str | None = None

    async def add_stake(
        self,
        amount: int,
        wallet: bittensor_wallet.Wallet | None = None,
    ) -> None:
        extrinsic = await self.subnet.client.subtensor.subtensor_module.add_stake(
            netuid=self.subnet.netuid,
            hotkey=self.hotkey,
            amount_staked=amount,
            wallet=wallet or self.subnet.client.wallet,
        )
        await extrinsic.wait_for_finalization()

    async def get(self, block_hash: str | None = None) -> Neuron | None:
        if self.uid is not None:
            uid = self.uid
        elif self.hotkey is not None:
            if not block_hash:
                block_hash = get_ctx_block_hash()

            uid = await self.subnet.client.subtensor.subtensor_module.Uids.get(
                self.subnet.netuid,
                self.hotkey,
                block_hash=block_hash,
            )

            if uid is None:
                return None
        else:
            raise ValueError

        neuron_info = await self.subnet.client.subtensor.neuron_info.get_neuron(
            self.subnet.netuid,
            uid,
            block_hash=block_hash,
        )

        if not neuron_info:
            return None

        neuron = Neuron.from_dict(
            neuron_info,
            subnet=self.subnet,
        )

        return neuron

    async def get_certificate(self, block_hash: str | None = None) -> NeuronCertificate | None:
        certificate = await self.subnet.client.subtensor.subtensor_module.NeuronCertificates.get(
            self.subnet.netuid,
            self.hotkey,
            block_hash=block_hash,
        )
        if certificate is not None:
            certificate["public_key"] = certificate["public_key"].removeprefix("0x")

        return certificate

    async def remove_stake(
        self,
        amount: int,
        wallet: bittensor_wallet.Wallet | None = None
    ) -> None:
        extrinsic = await self.subnet.client.subtensor.subtensor_module.remove_stake(
            netuid=self.subnet.netuid,
            hotkey=self.hotkey,
            amount_unstaked=amount,
            wallet=wallet or self.subnet.client.wallet,
        )
        await extrinsic.wait_for_finalization()
