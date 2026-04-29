from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
import time
import typing
from collections.abc import Iterable, Sequence
from typing import TextIO

import turbobt
from turbobt.substrate.pallets.state import StorageChangeSet

ROOT_NETUID = 0
FIXED_64_SCALE = 1 << 64
ROOT_ALPHA_SQRT_PRICE_BITS = FIXED_64_SCALE
DEFAULT_MAINNET_URI = "https://bittensor-finney.api.onfinality.io/public"
RAO_PER_TAO = 1_000_000_000

logger = logging.getLogger(__name__)
T = typing.TypeVar("T")
TimingObserver: typing.TypeAlias = typing.Callable[[tuple[str, float]], object]


def decode_bool_scale(value_hex: str | None) -> bool:
    if value_hex is None:
        return False

    return bool(bytes.fromhex(value_hex.removeprefix("0x"))[0])


def decode_fixed_u128_bits(value_hex: str | None) -> int | None:
    if value_hex is None:
        return None

    raw = bytes.fromhex(value_hex.removeprefix("0x"))
    if not raw:
        return None

    return int.from_bytes(raw, "little")


def fixed_u128_bits_to_float(bits: int) -> float:
    return bits / FIXED_64_SCALE


def alpha_price_rao_from_sqrt_bits(bits: int) -> int:
    price_u64f64_bits = (bits * bits) >> 64
    price_u96f32_bits = price_u64f64_bits >> 32
    return (price_u96f32_bits * RAO_PER_TAO) >> 32


def alpha_price_from_sqrt_bits(bits: int) -> str:
    rao = alpha_price_rao_from_sqrt_bits(bits)
    whole, fractional = divmod(rao, RAO_PER_TAO)
    return f"{whole}.{fractional:09d}"


def build_storage_key_map(
    subtensor: turbobt.Subtensor,
    pallet_name: str,
    storage_name: str,
    netuids: Iterable[int],
) -> dict[str, int]:
    pallet = subtensor._metadata.get_metadata_pallet(pallet_name)
    storage_function = pallet.get_storage_function(storage_name)

    return {
        subtensor.state._storage_key(
            pallet,
            storage_function,
            [netuid],
        ): netuid
        for netuid in netuids
    }


def decode_status_change_set(
    storage_change_set: StorageChangeSet,
    key_to_netuid: dict[str, int],
) -> dict[int, bool]:
    decoded: dict[int, bool] = {}

    for key, value in storage_change_set["changes"]:
        try:
            netuid = key_to_netuid[key]
        except KeyError:
            continue

        decoded[netuid] = decode_bool_scale(value)

    return decoded


def warn_for_non_v3_subnets(
    *,
    swap_v3_initialized: dict[int, bool],
) -> None:
    for netuid in sorted(swap_v3_initialized):
        if netuid == ROOT_NETUID:
            continue

        if not swap_v3_initialized.get(netuid, False):
            logger.warning("netuid %s does not have swap-v3 initialized", netuid)


async def run_measured_subtensor_call(
    interaction_name: str,
    call: typing.Callable[[], typing.Awaitable[T]],
    *,
    timer: typing.Callable[[], float] = time.perf_counter,
    observer: TimingObserver | None = None,
) -> tuple[T, float]:
    started_at = timer()
    result = await call()
    duration = round(timer() - started_at, 6)

    if observer is not None:
        observer((interaction_name, duration))

    return result, duration


def build_block_price_rows(
    *,
    block_numbers: Sequence[int],
    block_hashes: Sequence[str],
    netuids: Sequence[int],
    price_key_to_netuid: dict[str, int],
    price_changes: Sequence[StorageChangeSet],
) -> list[dict[str, int | str | None]]:
    updates_by_block: dict[str, dict[int, int | None]] = {}

    for storage_change_set in price_changes:
        updates: dict[int, int | None] = {}

        for key, value in storage_change_set["changes"]:
            try:
                netuid = price_key_to_netuid[key]
            except KeyError:
                continue

            updates[netuid] = decode_fixed_u128_bits(value)

        if updates:
            updates_by_block[storage_change_set["block"]] = updates

    current_bits: dict[int, int | None] = {
        ROOT_NETUID: ROOT_ALPHA_SQRT_PRICE_BITS,
    }
    rows: list[dict[str, int | str | None]] = []

    for block_number, block_hash in zip(block_numbers, block_hashes, strict=True):
        current_bits.update(updates_by_block.get(block_hash, {}))

        for netuid in netuids:
            bits = current_bits.get(netuid)
            rows.append(
                {
                    "block_number": block_number,
                    "block_hash": block_hash,
                    "netuid": netuid,
                    "alpha_price": (
                        alpha_price_from_sqrt_bits(bits) if bits is not None else None
                    ),
                    "alpha_sqrt_price_bits": bits,
                }
            )

    return rows


def alpha_price_text_to_rao(alpha_price: str) -> int:
    whole, fractional = alpha_price.split(".")
    return int(whole) * RAO_PER_TAO + int(fractional)


def _extract_runtime_price(entry: typing.Any) -> tuple[int, int]:
    if isinstance(entry, dict):
        return int(entry["netuid"]), int(entry["price"])

    return int(entry.netuid), int(entry.price)


async def verify_head_prices(
    subtensor: turbobt.Subtensor,
    *,
    block_hash: str,
    head_rows: dict[int, dict[str, str]],
    timer: typing.Callable[[], float] = time.perf_counter,
    observer: TimingObserver | None = None,
) -> list[tuple[int, int, int]]:
    runtime_prices, _ = await run_measured_subtensor_call(
        "SwapRuntimeApi.current_alpha_price_all",
        lambda: subtensor.api_call(
            "SwapRuntimeApi",
            "current_alpha_price_all",
            block_hash=block_hash,
        ),
        timer=timer,
        observer=observer,
    )
    expected_rao_by_netuid = dict(_extract_runtime_price(entry) for entry in runtime_prices)
    mismatches: list[tuple[int, int, int]] = []

    for netuid, row in sorted(head_rows.items()):
        observed_text = row["alpha_price"]
        if observed_text is None:
            continue

        observed_rao = alpha_price_text_to_rao(observed_text)
        expected_rao = RAO_PER_TAO if netuid == ROOT_NETUID else expected_rao_by_netuid.get(
            netuid
        )

        if expected_rao is None:
            continue

        if observed_rao != expected_rao:
            mismatches.append((netuid, observed_rao, expected_rao))

    return mismatches


async def collect_rows(
    *,
    uri: str,
    blocks: int,
    timing_observer: TimingObserver | None = None,
) -> list[dict[str, int | str | None]]:
    if blocks < 1:
        raise ValueError("blocks must be positive")

    async with turbobt.Subtensor(uri) as subtensor:
        _, _ = await run_measured_subtensor_call(
            "subtensor._init_runtime",
            subtensor._init_runtime,
            observer=timing_observer,
        )

        head_hash, _ = await run_measured_subtensor_call(
            "chain.getFinalizedHead",
            subtensor.chain.getFinalizedHead,
            observer=timing_observer,
        )
        if head_hash is None:
            raise RuntimeError("failed to resolve finalized head")

        head_header, _ = await run_measured_subtensor_call(
            "chain.getHeader",
            lambda: subtensor.chain.getHeader(head_hash),
            observer=timing_observer,
        )
        if head_header is None:
            raise RuntimeError("failed to resolve finalized head header")

        head_number = head_header["number"]
        start_number = max(0, head_number - (blocks - 1))
        block_numbers = list(range(start_number, head_number + 1))
        block_hashes, _ = await run_measured_subtensor_call(
            "chain.getBlockHash",
            lambda: subtensor.chain.getBlockHash(block_numbers),
            observer=timing_observer,
        )

        if (
            not isinstance(block_hashes, list)
            or len(block_hashes) != len(block_numbers)
            or any(block_hash is None for block_hash in block_hashes)
        ):
            raise RuntimeError("failed to resolve every block hash in the requested range")

        total_networks, _ = await run_measured_subtensor_call(
            "SubtensorModule.TotalNetworks.get",
            lambda: subtensor.subtensor_module.TotalNetworks.get(
                block_hash=head_hash,
            ),
            observer=timing_observer,
        )
        netuids = list(range(total_networks))
        dynamic_netuids = [netuid for netuid in netuids if netuid != ROOT_NETUID]

        price_key_to_netuid = build_storage_key_map(
            subtensor,
            "Swap",
            "AlphaSqrtPrice",
            dynamic_netuids,
        )
        initialized_key_to_netuid = build_storage_key_map(
            subtensor,
            "Swap",
            "SwapV3Initialized",
            dynamic_netuids,
        )

        head_status, _ = await run_measured_subtensor_call(
            "state.queryStorageAt",
            lambda: subtensor.state.queryStorageAt(
                list(initialized_key_to_netuid),
                block_hash=head_hash,
            ),
            observer=timing_observer,
        )
        head_status_change_set = (
            head_status[0] if head_status else {"block": head_hash, "changes": []}
        )
        swap_v3_initialized = decode_status_change_set(
            head_status_change_set,
            initialized_key_to_netuid,
        )

        for netuid in dynamic_netuids:
            swap_v3_initialized.setdefault(netuid, False)

        warn_for_non_v3_subnets(
            swap_v3_initialized=swap_v3_initialized,
        )

        price_changes = (
            (
                await run_measured_subtensor_call(
                    "state.queryStorage",
                    lambda: subtensor.state.queryStorage(
                        list(price_key_to_netuid),
                        from_block_hash=block_hashes[0],
                        to_block_hash=head_hash,
                    ),
                    observer=timing_observer,
                )
            )
            [0]
            if price_key_to_netuid
            else []
        )

    return build_block_price_rows(
        block_numbers=block_numbers,
        block_hashes=block_hashes,
        netuids=netuids,
        price_key_to_netuid=price_key_to_netuid,
        price_changes=price_changes,
    )


def write_rows_as_csv(
    rows: Sequence[dict[str, int | str | None]],
    output: TextIO,
) -> None:
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "block_number",
            "block_hash",
            "netuid",
            "alpha_price",
            "alpha_sqrt_price_bits",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print subnet alpha prices for the most recent blocks as CSV using "
            "Swap.AlphaSqrtPrice historical storage reads."
        )
    )
    parser.add_argument(
        "--uri",
        default=DEFAULT_MAINNET_URI,
        help=(
            "Subtensor endpoint or turbobt network alias. "
            f"Default: {DEFAULT_MAINNET_URI}"
        ),
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=25,
        help="Number of most recent blocks to print. Default: 25",
    )
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    timings: list[tuple[str, float]] = []
    rows = await collect_rows(
        uri=args.uri,
        blocks=args.blocks,
        timing_observer=timings.append,
    )
    write_rows_as_csv(rows, sys.stdout)
    for interaction_name, duration in timings:
        logger.info("%s took %.6fs", interaction_name, duration)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    asyncio.run(async_main(parse_args()))


if __name__ == "__main__":
    main()
