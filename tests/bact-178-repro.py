import asyncio
import logging
import os
from typing import Callable

# make tha race very probable
os.environ['TURBOBT_RETRIES'] = '10'
os.environ['WEBSOCKETS_BACKOFF_INITIAL_DELAY'] = '20'

import docker
import turbobt

# Subtensor configuration
SUBTENSOR_IP = "127.0.0.1"
SUBTENSOR_PORT = 9944

TEST_DURATION_SECONDS = 120


def get_coroutine_name():
    try:
        task = asyncio.current_task()
        if task:
            return task.get_name()
        else:
            return 'main'
    except RuntimeError:
        return 'no-event-loop'


# Custom logging filter to add coroutine context
class CoroutineFilter(logging.Filter):
    def filter(self, record):
        record.coro_name = get_coroutine_name()
        return True


coro_filter = CoroutineFilter()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(coro_name)s] - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

root_logger = logging.getLogger()
root_logger.addFilter(coro_filter)
for handler in root_logger.handlers:
    handler.addFilter(coro_filter)

logger = logging.getLogger(__name__)

async def get_block_with_pylon_like_timeout():
    subtensor_ws = f"ws://{SUBTENSOR_IP}:{SUBTENSOR_PORT}"
    logger.info(f"Connecting to subtensor via {subtensor_ws}")

    async with turbobt.Bittensor(subtensor_ws) as client:
        logger.info(f"Connected to subtensor at {subtensor_ws}")
        for x in range(TEST_DURATION_SECONDS):
            try:
                getting_block_task = asyncio.create_task(get_newest_block(client), name=get_coroutine_name() + '-get-block-task')
                if os.environ.get('SHIELD_TASK', '') == '1':
                    getting_block_task = asyncio.shield(getting_block_task)
                await asyncio.wait_for(getting_block_task, 2)
                await asyncio.sleep(1)
            except asyncio.TimeoutError as e:
                logger.error(f"Pylon-like timeout error? {e}", exc_info=True)


async def get_newest_block(client):
    try:
        current_block = await client.head.get()
        logger.info(f"Current Block Number: {current_block.number}, Block Hash: {current_block.hash}")
    except RuntimeError as e:
        logger.error(f"Got async generator failure? {e}")
    except Exception as e:
        logger.error(f"Error getting block from subtensor: {e}", exc_info=True)


async def loop_until_log_line_matches_predicate(container, predicate: Callable[[str], bool], timeout=60):
    """Wait for a specific log line in the container logs that matches the given predicate"""
    logger.info("Waiting for specific log line in container logs...")
    start_time = asyncio.get_event_loop().time()

    try:
        # Stream logs from the beginning;
        log_stream = container.logs(stream=True, follow=True)
        for log_line in log_stream:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Container did not produce matching log line within {timeout} seconds")

            try:
                line = log_line.decode('utf-8')
                logger.debug(f"Container log: {line.strip()}")
                if predicate(line):
                    logger.info("Found matching log line!")
                    return
                await asyncio.sleep(0)
            except Exception as e:
                logger.warning(f"Error decoding log line: {e}")
    except Exception as e:
        logger.error(f"Error streaming container logs: {e}")
        raise


async def wait_for_subtensor_node_ready(container):
    """Wait for the container to be ready by monitoring its logs"""
    def is_ready_log_line(line: str) -> bool:
        return "Prepared block for proposing at 1" in line

    await loop_until_log_line_matches_predicate(container, is_ready_log_line, timeout=60)
    logger.info("Subtensor node is running.")


async def main():
    subtensor_container = None
    try:

        failing_task = asyncio.create_task(get_block_with_pylon_like_timeout(), name='get-block-failing-with-async-generator-raised-StopAsyncIteration')
        await asyncio.sleep(10)

        # Start local subtensor node
        docker_client = docker.from_env()
        subtensor_container = docker_client.containers.run(
            "ghcr.io/opentensor/subtensor-localnet:devnet-ready",
            name="local_chain",
            ports={'9944/tcp': 9944, '9945/tcp': 9945},
            detach=True,
            auto_remove=True,
        )
        logger.info("Subtensor node started, waiting for it to be ready...")
        # Wait for the container to be ready by checking logs
        await wait_for_subtensor_node_ready(subtensor_container)

        succeeding_task = asyncio.create_task(get_block_with_pylon_like_timeout(), name='get-block-succeeding')
        await failing_task
        await succeeding_task
    finally:
        # Ensure cleanup happens even if something goes wrong
        if subtensor_container:
            subtensor_container.stop()


if __name__ == "__main__":
    asyncio.run(main())
