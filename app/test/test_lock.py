import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Create an asyncio lock
lock = asyncio.Lock()

async def async_function():
    """Async function that acquires the lock and runs."""
    async with lock:
        print("[ASYNC] Acquired lock")
        await asyncio.sleep(2)  # Simulate work
        print("[ASYNC] Released lock")

def threaded_function():
    """Threaded function that runs within the asyncio event loop and waits for the lock."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        async with lock:
            print("[THREAD] Acquired lock")
            await asyncio.sleep(3)  # Simulate work
            print("[THREAD] Released lock")

    loop.run_until_complete(run())

async def main():
    executor = ThreadPoolExecutor(max_workers=1)

    # Run the threaded function in a separate thread
    loop = asyncio.get_running_loop()
    thread_task = loop.run_in_executor(executor, threaded_function)

    # Run async function
    await async_function()

    # Wait for the thread to finish
    await thread_task

# Run the event loop
asyncio.run(main())
