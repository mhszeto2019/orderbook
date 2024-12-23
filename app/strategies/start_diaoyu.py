import subprocess

def start_subscriber(channel):
    cmd = ['python', 'diaoyu.py', channel]
    process = subprocess.Popen(cmd)
    return process

# Define the channels for each subscriber
channels = ['username:example_channel', 'username:example_channel2']

# Start a process for each channel
processes = []
for channel in channels:
    process = start_subscriber(channel)
    processes.append(process)

print("Subscribers started. Listening for messages... Press Ctrl+C to exit.")

# Wait for all processes to complete
try:
    for process in processes:
        process.wait()

except KeyboardInterrupt:
    print("Exiting...")

# Wait for a short period to ensure all processes have fully exited
import time
time.sleep(1)
