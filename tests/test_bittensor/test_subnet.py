import ipaddress

import pytest

from turbobt.neuron import AxonInfo, Neuron, PrometheusInfo
from turbobt.subnet import Subnet, SubnetReference
from turbobt.subtensor.pallets.subtensor_module import (
    CertificateAlgorithm,
    NeuronCertificate,
)


@pytest.mark.asyncio
async def test_get(mocked_subtensor, bittensor):
    mocked_subtensor.subnet_info.get_dynamic_info.return_value = {
        "subnet_name": "apex",
        "token_symbol": "α",
        "owner_hotkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "owner_coldkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "tempo": 100,
        "subnet_identity": None,
    }

    subnet_ref = bittensor.subnet(1)
    subnet = await subnet_ref.get()

    assert subnet == Subnet(
        client=bittensor,
        identity=None,
        name="apex",
        netuid=1,
        owner_coldkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        owner_hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        symbol="α",
        tempo=100,
    )


@pytest.mark.asyncio
async def test_get_hyperparameters(mocked_subtensor, bittensor):
    mocked_subtensor.subnet_info.get_subnet_hyperparams.return_value = {
        "activity_cutoff": 5000,
        "adjustment_alpha": 0,
        "adjustment_interval": 100,
        "alpha_high": 58982,
        "alpha_low": 45875,
        "bonds_moving_avg": 900000,
        "commit_reveal_period": 1,
        "commit_reveal_weights_enabled": False,
        "difficulty": 10000000,
        "immunity_period": 4096,
        "kappa": 32767,
        "liquid_alpha_enabled": False,
        "max_burn": 100000000000,
        "max_difficulty": 4611686018427387903,
        "max_regs_per_block": 1,
        "max_validators": 64,
        "max_weights_limit": 65535,
        "min_allowed_weights": 0,
        "min_burn": 500000,
        "min_difficulty": 10000000,
        "registration_allowed": True,
        "rho": 10,
        "serving_rate_limit": 50,
        "target_regs_per_interval": 2,
        "tempo": 100,
        "weights_rate_limit": 100,
        "weights_version": 0,
    }

    subnet_ref = bittensor.subnet(1)
    subnet_hyperparameters = await subnet_ref.get_hyperparameters()

    assert subnet_hyperparameters == {
        "activity_cutoff": 5000,
        "adjustment_alpha": 0,
        "adjustment_interval": 100,
        "alpha_high": 58982,
        "alpha_low": 45875,
        "bonds_moving_avg": 900000,
        "commit_reveal_period": 1,
        "commit_reveal_weights_enabled": False,
        "difficulty": 10000000,
        "immunity_period": 4096,
        "kappa": 32767,
        "liquid_alpha_enabled": False,
        "max_burn": 100000000000,
        "max_difficulty": 4611686018427387903,
        "max_regs_per_block": 1,
        "max_validators": 64,
        "max_weights_limit": 65535,
        "min_allowed_weights": 0,
        "min_burn": 500000,
        "min_difficulty": 10000000,
        "registration_allowed": True,
        "rho": 10,
        "serving_rate_limit": 50,
        "target_regs_per_interval": 2,
        "tempo": 100,
        "weights_rate_limit": 100,
        "weights_version": 0,
    }


@pytest.mark.asyncio
async def test_get_hyperparameters_v2(mocked_subtensor, bittensor):
    mocked_subtensor.subnet_info.get_subnet_hyperparams_v2.return_value = {
        "rho": 10,
        "kappa": 32767,
        "immunity_period": 4096,
        "min_allowed_weights": 0,
        "max_weights_limit": 65535,
        "tempo": 100,
        "min_difficulty": 10_000_000,
        "max_difficulty": 4_611_686_018_427_387_903,
        "weights_version": 0,
        "weights_rate_limit": 100,
        "adjustment_interval": 100,
        "activity_cutoff": 5000,
        "registration_allowed": True,
        "target_regs_per_interval": 2,
        "min_burn": 500_000,
        "max_burn": 100_000_000_000,
        "bonds_moving_avg": 900_000,
        "max_regs_per_block": 1,
        "serving_rate_limit": 50,
        "max_validators": 64,
        "adjustment_alpha": 0,
        "difficulty": 10_000_000,
        "commit_reveal_period": 1,
        "commit_reveal_weights_enabled": False,
        "alpha_high": 58_982,
        "alpha_low": 45_875,
        "liquid_alpha_enabled": False,
        "alpha_sigmoid_steepness": {
            "bits": 4_294_967_296_000,
        },
        "yuma_version": 1,
        "subnet_is_active": True,
        "transfers_enabled": True,
        "bonds_reset_enabled": False,
        "user_liquidity_enabled": False,
    }

    subnet_ref = bittensor.subnet(1)
    subnet_hyperparameters = await subnet_ref.get_hyperparameters_v2()

    assert subnet_hyperparameters == {
        "rho": 10,
        "kappa": 32767,
        "immunity_period": 4096,
        "min_allowed_weights": 0,
        "max_weights_limit": 65535,
        "tempo": 100,
        "min_difficulty": 10_000_000,
        "max_difficulty": 4_611_686_018_427_387_903,
        "weights_version": 0,
        "weights_rate_limit": 100,
        "adjustment_interval": 100,
        "activity_cutoff": 5000,
        "registration_allowed": True,
        "target_regs_per_interval": 2,
        "min_burn": 500_000,
        "max_burn": 100_000_000_000,
        "bonds_moving_avg": 900_000,
        "max_regs_per_block": 1,
        "serving_rate_limit": 50,
        "max_validators": 64,
        "adjustment_alpha": 0,
        "difficulty": 10_000_000,
        "commit_reveal_period": 1,
        "commit_reveal_weights_enabled": False,
        "alpha_high": 58_982,
        "alpha_low": 45_875,
        "liquid_alpha_enabled": False,
        "alpha_sigmoid_steepness": {
            "bits": 4_294_967_296_000,
        },
        "yuma_version": 1,
        "subnet_is_active": True,
        "transfers_enabled": True,
        "bonds_reset_enabled": False,
        "user_liquidity_enabled": False,
    }


@pytest.mark.asyncio
async def test_get_state(mocked_subtensor, bittensor):
    mocked_subtensor.subnet_info.get_subnet_state.return_value = {
        "active": [True],
        "alpha_stake": [1000000000],
        "block_at_registration": [0],
        "coldkeys": ["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"],
        "consensus": [0],
        "dividends": [0],
        "emission_history": [[0], [0]],
        "emission": [0],
        "hotkeys": ["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"],
        "incentives": [0],
        "last_update": [0],
        "netuid": 1,
        "pruning_score": [65535],
        "rank": [0],
        "tao_stake": [0],
        "total_stake": [1000000000],
        "trust": [0],
        "validator_permit": [True],
    }

    subnet_ref = bittensor.subnet(1)
    subnet_state = await subnet_ref.get_state()

    assert subnet_state == {
        "active": [True],
        "alpha_stake": [1000000000],
        "block_at_registration": [0],
        "coldkeys": ["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"],
        "consensus": [0],
        "dividends": [0],
        "emission_history": [[0], [0]],
        "emission": [0],
        "hotkeys": ["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"],
        "incentives": [0],
        "last_update": [0],
        "netuid": 1,
        "pruning_score": [65535],
        "rank": [0],
        "tao_stake": [0],
        "total_stake": [1000000000],
        "trust": [0],
        "validator_permit": [True],
    }


@pytest.mark.parametrize(
    "block_number,epoch",
    [
        (
            1000,
            range(719, 1080),
        ),
        (
            1079,
            range(719, 1080),
        ),
        (
            1080,
            range(1080, 1441),
        ),
        (
            1081,
            range(1080, 1441),
        ),
    ],
)
@pytest.mark.asyncio
async def test_subnet_epoch(mocked_subtensor, bittensor, block_number, epoch):
    mocked_subtensor.subnet_info.get_dynamic_info.return_value = {
        "subnet_name": "apex",
        "token_symbol": "α",
        "owner_hotkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "owner_coldkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "tempo": 360,
        "subnet_identity": None,
    }

    subnet = await bittensor.subnet(1).get()

    assert subnet.epoch(block_number) == epoch


@pytest.mark.asyncio
async def test_list_neurons(mocked_subtensor, bittensor):
    mocked_subtensor.neuron_info.get_neurons_lite.return_value = [
        {
            "hotkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            "coldkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            "uid": 0,
            "netuid": 1,
            "active": True,
            "axon_info": {
                "block": 0,
                "version": 0,
                "ip": 0,
                "port": 0,
                "ip_type": 0,
                "protocol": 0,
                "placeholder1": 0,
                "placeholder2": 0,
            },
            "prometheus_info": {
                "block": 0,
                "version": 0,
                "ip": 0,
                "port": 0,
                "ip_type": 0,
            },
            "stake": {
                "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM": 1000000000,
            },
            "rank": 0,
            "emission": 0,
            "incentive": 0,
            "consensus": 0,
            "trust": 0,
            "validator_trust": 0,
            "dividends": 0,
            "last_update": 0,
            "validator_permit": False,
            "pruning_score": 0,
        },
    ]

    subnet_ref = bittensor.subnet(1)
    subnet_neurons = await subnet_ref.list_neurons()

    assert subnet_neurons == [
        Neuron(
            active=True,
            axon_info=AxonInfo(
                ip=ipaddress.IPv4Address("0.0.0.0"),  # noqa: S104
                port=0,
                protocol=0,
            ),
            coldkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            consensus=0,
            dividends=0,
            emission=0,
            hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            incentive=0,
            last_update=0,
            prometheus_info=PrometheusInfo(
                ip=ipaddress.IPv4Address("0.0.0.0"),  # noqa: S104
                port=0,
            ),
            pruning_score=0,
            rank=0,
            stake=1.0,
            subnet=SubnetReference(
                client=bittensor,
                netuid=1,
            ),
            trust=0,
            uid=0,
            validator_permit=False,
            validator_trust=0,
        ),
    ]


@pytest.mark.asyncio
async def test_list_validators(mocked_subtensor, bittensor):
    mocked_subtensor.chain.getBlockHash.return_value = (
        "0x2bb80cc429296b4da191bcec87d4b526ca0e407b4756f2a387a87d3b8e26ae42"
    )
    mocked_subtensor.subnet_info.get_subnet_state.return_value = {
        "active": [True],
        "alpha_stake": [1000000000],
        "block_at_registration": [0],
        "coldkeys": ["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"],
        "consensus": [0],
        "dividends": [0],
        "emission_history": [[0], [0]],
        "emission": [0],
        "hotkeys": ["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"],
        "incentives": [0],
        "last_update": [0],
        "netuid": 1,
        "pruning_score": [65535],
        "rank": [0],
        "tao_stake": [0],
        "total_stake": [1000000000],
        "trust": [0],
        "validator_permit": [True],
    }
    mocked_subtensor.subnet_info.get_subnet_hyperparams.return_value = {
        "activity_cutoff": 5000,
        "adjustment_alpha": 0,
        "adjustment_interval": 100,
        "alpha_high": 58982,
        "alpha_low": 45875,
        "bonds_moving_avg": 900000,
        "commit_reveal_period": 1,
        "commit_reveal_weights_enabled": False,
        "difficulty": 10000000,
        "immunity_period": 4096,
        "kappa": 32767,
        "liquid_alpha_enabled": False,
        "max_burn": 100000000000,
        "max_difficulty": 4611686018427387903,
        "max_regs_per_block": 1,
        "max_validators": 64,
        "max_weights_limit": 65535,
        "min_allowed_weights": 0,
        "min_burn": 500000,
        "min_difficulty": 10000000,
        "registration_allowed": True,
        "rho": 10,
        "serving_rate_limit": 50,
        "target_regs_per_interval": 2,
        "tempo": 100,
        "weights_rate_limit": 100,
        "weights_version": 0,
    }
    mocked_subtensor.neuron_info.get_neurons_lite.return_value = [
        {
            "hotkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            "coldkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            "uid": 0,
            "netuid": 1,
            "active": True,
            "axon_info": {
                "block": 0,
                "version": 0,
                "ip": 0,
                "port": 0,
                "ip_type": 0,
                "protocol": 0,
                "placeholder1": 0,
                "placeholder2": 0,
            },
            "prometheus_info": {
                "block": 0,
                "version": 0,
                "ip": 0,
                "port": 0,
                "ip_type": 0,
            },
            "stake": {
                "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM": 1000000000,
            },
            "rank": 0,
            "emission": 0,
            "incentive": 0,
            "consensus": 0,
            "trust": 0,
            "validator_trust": 0,
            "dividends": 0,
            "last_update": 0,
            "validator_permit": False,
            "pruning_score": 0,
        },
    ]
    mocked_subtensor.state.getStorage.return_value = 1_000_000

    subnet_ref = bittensor.subnet(1)
    subnet_validators = await subnet_ref.list_validators()

    assert subnet_validators == [
        Neuron(
            active=True,
            axon_info=AxonInfo(
                ip=ipaddress.IPv4Address("0.0.0.0"),  # noqa: S104
                port=0,
                protocol=0,
            ),
            coldkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            consensus=0,
            dividends=0,
            emission=0,
            hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
            incentive=0,
            last_update=0,
            prometheus_info=PrometheusInfo(
                ip=ipaddress.IPv4Address("0.0.0.0"),  # noqa: S104
                port=0,
            ),
            pruning_score=0,
            rank=0,
            stake=1.0,
            subnet=SubnetReference(
                client=bittensor,
                netuid=1,
            ),
            trust=0,
            uid=0,
            validator_permit=False,
            validator_trust=0,
        ),
    ]


@pytest.mark.asyncio
async def test_register_subnet(mocked_subtensor, bittensor, alice_wallet):
    await bittensor.subnets.register(
        wallet=alice_wallet,
    )

    mocked_subtensor.subtensor_module.register_network.assert_awaited_once_with(
        hotkey="5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
        mechid=1,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_get_certificates(mocked_subtensor, bittensor):
    # Mock certificate data for each neuron
    mock_cert1 = NeuronCertificate(
        algorithm=CertificateAlgorithm.ED25519,
        public_key="0x1234567890abcdef",
    )
    mock_cert2 = NeuronCertificate(
        algorithm=CertificateAlgorithm.ED25519,
        public_key="0xfedcba0987654321",
    )

    # Mock the fetch method that returns list of tuples in format: [((netuid, hotkey), certificate), ...]
    mock_certificates = [
        (("netuid", "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"), mock_cert1),
        (("netuid", "5D34dL5prEUaGNQtPPZ3yN5Y6BnkfXunKXXz6fo7ZJbLwRRH"), mock_cert2),
    ]

    mocked_subtensor.subtensor_module.NeuronCertificates.fetch.return_value = (
        mock_certificates
    )

    subnet = await bittensor.subnet(1).get()
    certificates = await subnet.neurons.get_certificates()

    # Verify the result - public_key should have "0x" stripped
    expected_certificates = {
        "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM": NeuronCertificate(
            algorithm=CertificateAlgorithm.ED25519,
            public_key="1234567890abcdef",
        ),
        "5D34dL5prEUaGNQtPPZ3yN5Y6BnkfXunKXXz6fo7ZJbLwRRH": NeuronCertificate(
            algorithm=CertificateAlgorithm.ED25519,
            public_key="fedcba0987654321",
        ),
    }

    assert certificates == expected_certificates


@pytest.mark.asyncio
async def test_get_certificates_with_block_hash(mocked_subtensor, bittensor):
    mock_cert = NeuronCertificate(
        algorithm=CertificateAlgorithm.ED25519,
        public_key="0x1234567890abcdef",
    )

    # Mock the fetch method that returns list of tuples in format: [((netuid, hotkey), certificate), ...]
    mock_certificates = [
        (("netuid", "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"), mock_cert),
    ]

    mocked_subtensor.subtensor_module.NeuronCertificates.fetch.return_value = (
        mock_certificates
    )

    subnet = await bittensor.subnet(1).get()
    block_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    certificates = await subnet.neurons.get_certificates(block_hash=block_hash)

    # Verify that fetch was called with the block_hash
    mocked_subtensor.subtensor_module.NeuronCertificates.fetch.assert_called_with(
        1, block_hash=block_hash
    )

    expected_certificates = {
        "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM": NeuronCertificate(
            algorithm=CertificateAlgorithm.ED25519,
            public_key="1234567890abcdef",  # "0x" prefix stripped
        ),
    }

    assert certificates == expected_certificates


@pytest.mark.asyncio
async def test_get_certificates_empty_neurons(mocked_subtensor, bittensor):
    # Mock empty certificates list from fetch
    mocked_subtensor.subtensor_module.NeuronCertificates.fetch.return_value = []

    subnet = await bittensor.subnet(1).get()
    certificates = await subnet.neurons.get_certificates()

    assert certificates == {}


@pytest.mark.asyncio
async def test_generate_certificate_keypair_success(
    mocker, mocked_subtensor, bittensor, alice_wallet, neuron
):
    subnet = await bittensor.subnet(1).get()

    # Mock the subnet.get_neuron method
    mock_get_neuron = mocker.patch.object(subnet, "get_neuron", return_value=neuron)
    # Mock the serve method to avoid actual serving
    mock_serve = mocker.patch.object(
        subnet.neurons, "serve", new_callable=mocker.AsyncMock
    )

    keypair = await subnet.neurons.generate_certificate_keypair()

    # Verify that get_neuron was called with the alice_wallet's ss58_address
    mock_get_neuron.assert_called_once_with(alice_wallet.hotkey.ss58_address)

    # Verify that serve was called with the certificate
    mock_serve.assert_called_once()
    call_args = mock_serve.call_args
    assert call_args[0][0] == "192.168.1.1"  # ip
    assert call_args[0][1] == 8080  # port
    assert "certificate" in call_args[1]
    assert call_args[1]["timeout"] is None

    # Verify the returned keypair structure
    assert isinstance(keypair, dict)
    assert "algorithm" in keypair
    assert "public_key" in keypair
    assert "private_key" in keypair
    assert keypair["algorithm"] == CertificateAlgorithm.ED25519


@pytest.mark.asyncio
async def test_generate_certificate_keypair_with_custom_algorithm(
    mocker, mocked_subtensor, bittensor, alice_wallet, neuron
):
    subnet = await bittensor.subnet(1).get()

    # Mock the subnet.get_neuron method
    mocker.patch.object(subnet, "get_neuron", return_value=neuron)
    # Mock the serve method to avoid actual serving
    mock_serve = mocker.patch.object(
        subnet.neurons, "serve", new_callable=mocker.AsyncMock
    )

    keypair = await subnet.neurons.generate_certificate_keypair(
        algorithm=CertificateAlgorithm.ED25519, timeout=30.0
    )

    # Verify that serve was called with the timeout
    mock_serve.assert_called_once()
    call_args = mock_serve.call_args
    assert call_args[1]["timeout"] == 30.0

    # Verify the algorithm in the returned keypair
    assert keypair["algorithm"] == CertificateAlgorithm.ED25519


@pytest.mark.asyncio
async def test_generate_certificate_keypair_neuron_not_found(
    mocker, mocked_subtensor, bittensor, alice_wallet
):
    subnet = await bittensor.subnet(1).get()

    # Mock the subnet.get_neuron method to return None
    mock_get_neuron = mocker.patch.object(subnet, "get_neuron", return_value=None)

    keypair = await subnet.neurons.generate_certificate_keypair()

    # Verify that get_neuron was called with alice_wallet's ss58_address
    mock_get_neuron.assert_called_once_with(alice_wallet.hotkey.ss58_address)

    # Verify that None is returned when neuron is not found
    assert keypair is None
