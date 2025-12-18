from __future__ import annotations

import asyncio
import dataclasses
import typing

import bittensor_drand
import bittensor_wallet
import scalecodec.utils.ss58
from ecies.config import EllipticCurve
from ecies.keys import PrivateKey as EciesPrivateKey

from turbobt.subtensor.runtime.subnet_info import (
    SubnetHyperparams,
    SubnetHyperparamsV2,
    SubnetState,
)
from turbobt.subtensor.types import HotKey, Uid

from .block import get_ctx_block_hash
from .neuron import (
    AxonProtocolEnum,
    Neuron,
    NeuronReference,
)
from .substrate._scalecodec import (
    float_to_u16_proportion,
    u16_proportion_to_float,
)
from .subtensor.pallets.subtensor_module import (
    CertificateAlgorithm,
    NeuronCertificate,
    NeuronCertificateKeypair,
)

if typing.TYPE_CHECKING:
    from .client import Bittensor


# TODO
BITTENSOR_VERSION = (9, 3, 0)
BITTENSOR_VERSION_INT = sum(
    e * (1000**i) for i, e in enumerate(reversed(BITTENSOR_VERSION))
)


class SubnetCommitments:
    def __init__(self, subnet: Subnet, client: Bittensor):
        self.subnet = subnet
        self.client = client

    async def get(self, hotkey: str, block_hash: str | None = None) -> bytes | None:
        commitments = await self.client.subtensor.commitments.CommitmentOf.get(
            self.subnet.netuid,
            hotkey,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if not commitments:
            return None

        return next(
            bytes.fromhex(value[2:] or "")
            for field in commitments["info"]["fields"]
            for value in field.values()
        )

    async def fetch(self, block_hash: str | None = None) -> dict[str, bytes]:
        commitments = await self.client.subtensor.commitments.CommitmentOf.fetch(
            self.subnet.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if not commitments:
            return {}

        return {
            hotkey: next(
                bytes.fromhex(value[2:] or "")
                for field in value["info"]["fields"]
                for value in field.values()
            )
            for (netuid, hotkey), value in commitments
        }

    async def set(
        self,
        data: bytes,
        wallet: bittensor_wallet.Wallet | None = None,
    ):
        return await self.client.subtensor.commitments.set_commitment(
            self.subnet.netuid,
            {
                "fields": [
                    [
                        {
                            f"Raw{len(data)}": data,
                        },
                    ],
                ],
            },
            wallet=wallet or self.client.wallet,
        )


class SubnetNeurons:
    def __init__(self, subnet: Subnet):
        self.subnet = subnet

    def __getitem__(self, key: int | str) -> NeuronReference:
        if isinstance(key, str):
            return NeuronReference(
                subnet=self.subnet,
                hotkey=key,
            )

        return NeuronReference(
            subnet=self.subnet,
            uid=key,
        )

    async def __aiter__(self):
        return iter(await self.all())

    async def register(
        self,
        hotkey: bittensor_wallet.Keypair,
        *,
        timeout: float | None = None,
        wallet: bittensor_wallet.Wallet | None = None,
    ) -> None:
        if self.subnet.netuid == 0:
            extrinsic = await self.subnet.client.subtensor.subtensor_module.root_register(
                hotkey=hotkey.ss58_address,
                wallet=wallet or self.subnet.client.wallet,
            )
        else:
            extrinsic = await self.subnet.client.subtensor.subtensor_module.burned_register(
                netuid=self.subnet.netuid,
                hotkey=hotkey.ss58_address,
                wallet=wallet or self.subnet.client.wallet,
            )

        async with asyncio.timeout(timeout):
            await extrinsic.wait_for_finalization()

    async def serve(
        self,
        ip: str,
        port: int,
        certificate: NeuronCertificate | bytes | None = None,
        timeout: float | None = None,
        wallet: bittensor_wallet.Wallet | None = None,
    ):
        if certificate:
            if not isinstance(certificate, bytes):
                certificate = bytes([certificate["algorithm"]]) + bytes.fromhex(certificate["public_key"])

            extrinsic = await self.subnet.client.subtensor.subtensor_module.serve_axon_tls(
                certificate=certificate,
                ip=ip,
                netuid=self.subnet.netuid,
                port=port,
                protocol=AxonProtocolEnum.HTTP,
                version=BITTENSOR_VERSION_INT,
                wallet=wallet or self.subnet.client.wallet,
            )
        else:
            extrinsic = await self.subnet.client.subtensor.subtensor_module.serve_axon(
                ip=ip,
                netuid=self.subnet.netuid,
                port=port,
                protocol=AxonProtocolEnum.HTTP,
                version=BITTENSOR_VERSION_INT,
                wallet=wallet or self.subnet.client.wallet,
            )

        async with asyncio.timeout(timeout):
            await extrinsic.wait_for_finalization()

    async def get_certificates(self, block_hash: str | None = None) -> dict[HotKey, NeuronCertificate]:
        def strip_0x(certificate: NeuronCertificate) -> NeuronCertificate:
            certificate["public_key"] = certificate["public_key"].removeprefix("0x")
            return certificate

        certificates = await self.subnet.client.subtensor.subtensor_module.NeuronCertificates.fetch(
            self.subnet.netuid,
            block_hash=block_hash,
        )

        return {
            elem[0][1]: strip_0x(elem[1])
            for elem in certificates
        }

    async def generate_certificate_keypair(
        self,
        algorithm: CertificateAlgorithm = CertificateAlgorithm.ED25519,
        timeout: float | None = None,
    ) -> NeuronCertificateKeypair | None:
        neuron = await self.subnet.get_neuron(self.subnet.client.wallet.hotkey.ss58_address)
        if neuron is None:
            return None

        curve = typing.cast(EllipticCurve, algorithm.name.lower())
        private_key = EciesPrivateKey(curve)
        private_key_hex = private_key.to_hex()
        public_key_hex = private_key.public_key.to_hex()
        certificate = NeuronCertificate(
            algorithm=algorithm,
            public_key=public_key_hex,
        )

        await self.serve(
            str(neuron.axon_info.ip),
            neuron.axon_info.port,
            certificate=certificate,
            timeout=timeout,
        )

        return NeuronCertificateKeypair(
            algorithm=algorithm,
            public_key=public_key_hex,
            private_key=private_key_hex,
        )

    async def all(self, block_hash: str | None = None) -> list[Neuron]:
        neurons = await self.subnet.client.subtensor.neuron_info.get_neurons_lite(
            self.subnet.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if neurons is None:
            return []

        return [
            Neuron.from_dict(
                neuron,
                subnet=self.subnet,
            )
            for neuron in neurons
        ]

    async def validators(self, block_hash: str | None = None) -> list[Neuron]:
        if not block_hash:
            block_hash = get_ctx_block_hash()

        if not block_hash:
            block_hash = await self.subnet.client.subtensor.chain.getBlockHash()

        neurons, state, hyperparameters, stake_threshold = await asyncio.gather(
            self.all(block_hash),
            self.subnet.get_state(block_hash),
            self.subnet.get_hyperparameters(block_hash),
            self.subnet.client.subtensor.state.getStorage(
                "SubtensorModule.StakeThreshold",
                block_hash=block_hash,
            ),
        )

        # https://github.com/opentensor/subtensor/blob/main/pallets/subtensor/src/epoch/math.rs#L235
        stakes = sorted(
            (total_stake, hotkey)
            for hotkey, total_stake in zip(state["hotkeys"], state["total_stake"])
            if total_stake >= stake_threshold
        )
        stakes = stakes[-hyperparameters["max_validators"] :]
        stakes, hotkeys = zip(*stakes)

        hotkeys = frozenset(hotkeys)

        # TODO return sorted?
        return [neuron for neuron in neurons if neuron.hotkey in hotkeys]


class WeightsCommited(typing.NamedTuple):
    block: int
    commit: bytes
    reveal_round: int


class SubnetWeights:
    def __init__(self, subnet: SubnetReference):
        self.subnet = subnet
        self.client = subnet.client

    async def set(
        self,
        weights: dict[int, float],
        version_key: int = BITTENSOR_VERSION_INT,
        wallet: bittensor_wallet.Wallet | None = None,
    ) -> None:
        weights = self._normalize(weights)

        try:
            uids, weights = zip(*weights.items())
        except ValueError:
            uids, weights = [], []

        extrinsic = await self.client.subtensor.subtensor_module.set_weights(
            self.subnet.netuid,
            list(uids),
            list(weights),
            version_key=version_key,
            wallet=wallet or self.subnet.client.wallet,
        )

        await extrinsic.wait_for_finalization()

    async def commit(
        self,
        weights: dict[int, float],
        version_key: int = BITTENSOR_VERSION_INT,
        wallet: bittensor_wallet.Wallet | None = None,
        block_time: int = 12,
    ) -> int:
        weights = self._normalize(weights)

        try:
            uids, weights = zip(*weights.items())
        except ValueError:
            uids, weights = [], []

        async with self.client.blocks[-1] as block:
            hyperparameters = await self.subnet.get_hyperparameters()

            commit, reveal_round = bittensor_drand.get_encrypted_commit(
                uids,
                weights,
                version_key=version_key,
                tempo=hyperparameters["tempo"],
                current_block=block.number,
                netuid=self.subnet.netuid,
                subnet_reveal_period_epochs=hyperparameters["commit_reveal_period"],
                block_time=block_time,
                hotkey=self.subnet.client.wallet.hotkey.public_key,
            )

        extrinsic = (
            await self.client.subtensor.subtensor_module.commit_timelocked_weights(
                self.subnet.netuid,
                commit,
                reveal_round,
                commit_reveal_version=4,
                wallet=wallet or self.subnet.client.wallet,
            )
        )

        await extrinsic.wait_for_finalization()

        return reveal_round

    async def get(self, uid: int, block_hash: str | None = None) -> dict[Uid, float]:
        weights = await self.client.subtensor.subtensor_module.Weights.get(
            self.subnet.netuid,
            uid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if not weights:
            return {}

        return {uid: u16_proportion_to_float(weight) for uid, weight in weights}

    async def fetch(self, block_hash: str | None = None) -> dict[Uid, dict[Uid, float]]:
        weights = await self.client.subtensor.subtensor_module.Weights.fetch(
            self.subnet.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if not weights:
            return {}

        return {
            validator_uid: {
                uid: u16_proportion_to_float(weight) for uid, weight in zipped_weights
            }
            for (netuid, validator_uid), zipped_weights in weights
        }

    async def fetch_pending(
        self,
        block_hash: str | None = None,
    ) -> dict[
        int,
        dict[
            HotKey,
            tuple[bytes, int],
        ],
    ]:
        weights = await self.client.subtensor.subtensor_module.TimelockedWeightCommits.fetch(
            self.subnet.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if not weights:
            return {}

        return {
            reveal_round: {
                scalecodec.utils.ss58.ss58_encode(hotkey): WeightsCommited(
                    commit_block,
                    bytes.fromhex(commit[2:]),
                    round_number,
                )
                for hotkey, commit_block, commit, round_number in commits
            }
            for (netuid, reveal_round), commits in weights
        }

    def _normalize(self, weights: dict[int, float]) -> dict[int, int]:
        try:
            max_weight = max(weights.values())
        except ValueError:
            return {}

        if not max_weight:
            return {
                uid: 0
                for uid in weights
            }

        return {
            uid: float_to_u16_proportion(weight / max_weight)
            for uid, weight in weights.items()
        }


@dataclasses.dataclass
class SubnetReference:
    netuid: int

    client: dataclasses.InitVar[Bittensor]

    def __post_init__(self, client: Bittensor):
        self.client = client
        self.commitments = SubnetCommitments(self, self.client)
        self.neurons = SubnetNeurons(self)
        self.weights = SubnetWeights(self)

    async def get(self, block_hash: str | None = None):
        dynamic_info = await self.client.subtensor.subnet_info.get_dynamic_info(
            self.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

        if not dynamic_info:
            return None

        subnet = Subnet(
            client=self.client,
            netuid=self.netuid,
            name=dynamic_info["subnet_name"],
            symbol=dynamic_info["token_symbol"],
            owner_coldkey=dynamic_info["owner_coldkey"],
            owner_hotkey=dynamic_info["owner_hotkey"],
            tempo=dynamic_info["tempo"],
            identity=dynamic_info["subnet_identity"],
        )

        return subnet

    async def get_hyperparameters(self, block_hash: str | None = None) -> SubnetHyperparams | None:
        return await self.client.subtensor.subnet_info.get_subnet_hyperparams(
            self.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

    async def get_hyperparameters_v2(self, block_hash: str | None = None) -> SubnetHyperparamsV2 | None:
        return await self.client.subtensor.subnet_info.get_subnet_hyperparams_v2(
            self.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

    async def get_neuron(
        self,
        key: str | int,
        block_hash: str | None = None,
    ) -> Neuron | None:
        if isinstance(key, str):
            uid = None
            hotkey = key
        elif isinstance(key, int):
            uid = key
            hotkey = None
        else:
            raise TypeError

        return await self.neuron(uid, hotkey).get(block_hash)

    async def get_state(self, block_hash: str | None = None) -> SubnetState | None:
        return await self.client.subtensor.subnet_info.get_subnet_state(
            self.netuid,
            block_hash=block_hash or get_ctx_block_hash(),
        )

    async def list_neurons(self, block_hash: str | None = None) -> list[Neuron]:
        return await self.neurons.all(block_hash)

    async def list_validators(self, block_hash: str | None = None) -> list[Neuron]:
        return await self.neurons.validators(block_hash)

    def neuron(
        self,
        uid: int | None = None,
        hotkey: str | None = None,
    ) -> NeuronReference:
        return NeuronReference(
            self,
            uid=uid,
            hotkey=hotkey,
        )


@dataclasses.dataclass(
    kw_only=True,
    order=True,
)
class Subnet(SubnetReference):
    netuid: int
    name: str = dataclasses.field(compare=False)
    symbol: str = dataclasses.field(compare=False, repr=False)
    tempo: int = dataclasses.field(compare=False, repr=False)
    owner_hotkey: str = dataclasses.field(compare=False, repr=False)
    owner_coldkey: str = dataclasses.field(compare=False, repr=False)
    identity: dict[str, str] = dataclasses.field(compare=False, repr=False)  # empty?

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self.neurons = SubnetNeurons(self)

    def epoch(self, block_number: int) -> range:
        """
        The logic from Subtensor's Rust function:
            pub fn blocks_until_next_epoch(netuid: NetUid, tempo: u16, block_number: u64) -> u64

        See https://github.com/opentensor/subtensor/blob/f8db5d06c0439d4fb5db66be3632e4d89a8829c0/pallets/subtensor/src/coinbase/run_coinbase.rs#L846
        """

        netuid_plus_one = self.netuid + 1
        tempo_plus_one = self.tempo + 1
        adjusted_block = block_number + netuid_plus_one
        remainder = adjusted_block % tempo_plus_one

        if remainder == self.tempo:
            remainder = -1

        return range(
            block_number - remainder - 1,
            block_number - remainder + self.tempo,
        )


class Subnets:
    def __init__(self, client: Bittensor):
        self.client = client

    def __getitem__(self, netuid) -> SubnetReference:
        return SubnetReference(netuid, self.client)

    async def count(self):
        return await self.client.subtensor.subtensor_module.TotalNetworks.get()

    async def get(self, netuid):
        return Subnet(netuid, self._subtensor)

    # TODO create?
    async def register(self, wallet=None, **kwargs):
        wallet = wallet or self.client.wallet

        # register_network_with_identity
        extrinsic = await self.client.subtensor.subtensor_module.register_network(
            hotkey=wallet.hotkey.ss58_address,
            mechid=1,
            wallet=wallet,
        )

        async with asyncio.timeout(60):
            await extrinsic.wait_for_finalization()

        # return SubnetReference(None, self._subtensor) # TODO id
