"""Generate legacy wallets on demand and verify native v11 signing compatibility."""

import json
import subprocess
import sys

import pytest
from bittensor.keyfiles import Keypair
from bittensor.wallet import Wallet


@pytest.fixture(
    scope="module",
    params=[
        pytest.param("legacy", id="legacy_without_crypto_type"),
        pytest.param("10.5", id="bittensor_10_5_cli"),
    ],
)
def generated_legacy_wallet(request, tmp_path_factory):
    """Create each format with its producer, independently of the reader under test."""
    path = tmp_path_factory.mktemp(f"wallet_{request.param}")
    name = "compatibility"
    packages = {
        "legacy": ["bittensor-wallet==4.0.1"],
        "10.5": [
            "bittensor[cli]==10.5.0",
            "bittensor-cli==9.22.0",
            "bittensor-wallet==4.1.0",
        ],
    }
    command = ["uv", "run", "--isolated", "--no-project", "--python", sys.executable]
    for package in packages[request.param]:
        command.extend(["--with", package])

    def run(*args):
        try:
            subprocess.run(
                [*command, *args],
                check=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.CalledProcessError as exc:
            pytest.fail(f"Wallet generation failed:\n{exc.stdout}\n{exc.stderr}")

    if request.param == "legacy":
        run(
            "python",
            "-c",
            "import sys; from bittensor_wallet import Wallet; "
            "w = Wallet(name=sys.argv[1], path=sys.argv[2], hotkey='default'); "
            "w.create_new_coldkey(use_password=False); "
            "w.create_new_hotkey(use_password=False)",
            name,
            str(path),
        )
    else:
        wallet_args = [
            "--wallet-name",
            name,
            "--hotkey",
            "default",
            "--wallet-path",
            str(path),
            "--n-words",
            "12",
        ]
        run("btcli", "wallet", "new-coldkey", *wallet_args, "--no-use-password")
        run("btcli", "wallet", "new-hotkey", *wallet_args)

    wallet_dir = path / name
    original_files = {p: p.read_bytes() for p in wallet_dir.rglob("*") if p.is_file()}
    coldkey_data = json.loads((wallet_dir / "coldkeypub.txt").read_text())
    hotkey_data = json.loads((wallet_dir / "hotkeys/default").read_text())
    # Read addresses from the producer's JSON, not from the reader being tested.
    # Also ensure the legacy case genuinely exercises the old serialization.
    assert ("cryptoType" in hotkey_data) == (request.param != "legacy")
    return (
        Wallet(name=name, path=str(path)),
        hotkey_data["ss58Address"],
        coldkey_data["ss58Address"],
        original_files,
    )


@pytest.mark.parametrize("signer", ["coldkey", "hotkey"])
@pytest.mark.asyncio
async def test_legacy_wallet_signs_extrinsic(
    substrate, mocked_transport, runtime, generated_legacy_wallet, signer
):
    wallet, hotkey, coldkey, original_files = generated_legacy_wallet
    assert wallet.hotkey.ss58_address == hotkey
    assert wallet.coldkeypub.ss58_address == coldkey
    assert wallet.coldkey.ss58_address == coldkey
    key = getattr(wallet, signer)
    genesis_hash = bytes.fromhex("ab" * 32)
    mocked_transport.responses.update(
        {
            "system_accountNextIndex": {"result": 1},
            "chain_getBlockHash": {"result": "0x" + genesis_hash.hex()},
            "author_submitAndWatchExtrinsic": {"result": "wallet-signature-test"},
        }
    )

    result = await substrate.author.submitAndWatchExtrinsic(
        "SubtensorModule",
        "register_network",
        {"hotkey": hotkey, "mechid": 1},
        key=key,
        era=None,
    )

    assert result.subscription.id == "wallet-signature-test"
    assert result.extrinsic.value["account_id"] == "0x" + key.public_key.hex()
    assert result.extrinsic.value["signature_version"] == 1
    signature = bytes.fromhex(
        result.extrinsic.value["signature"]["Sr25519"].removeprefix("0x")
    )
    # Reconstruct this runtime's SCALE signing payload independently: call, immortal
    # era, compact nonce=1, compact tip=0, disabled metadata mode, runtime versions,
    # genesis + mortality hashes, and absent metadata hash.
    call = bytes(result.extrinsic.value_object["call"].data.data)
    payload = (
        call
        + bytes.fromhex("00040000")
        + runtime["specVersion"].to_bytes(4, "little")
        + runtime["transactionVersion"].to_bytes(4, "little")
        + genesis_hash * 2
        + b"\x00"
    )
    verifier = Keypair(ss58_address=key.ss58_address)
    assert verifier.verify(payload, signature)
    assert not verifier.verify(payload + b"tampered", signature)
    assert {p: p.read_bytes() for p in original_files} == original_files
