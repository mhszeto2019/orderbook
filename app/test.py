import asyncio
import tkinter as tk
import websockets

# Set your WebSocket URLs for both exchanges
EXCHANGE_1_URL = "wss://example.com/exchange1"
EXCHANGE_2_URL = "wss://example.com/exchange2"

class WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.data = None

    async def listen_to_data(self, data_queue):
        """Connects to the WebSocket and listens for incoming data."""
        async with websockets.connect(self.url) as ws:
            while True:
                data = await ws.recv()
                print(f"Data from {self.url}: {data}")
                self.data = data
                await data_queue.put((self.url, data))  # Send data to shared queue


class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading App")

        # Initialize the target value with an empty string
        self.target_value = tk.StringVar()
        self.current_target = None  # Holds the updated target for comparisons

        # UI Elements
        tk.Label(root, text="Target Value:").pack()
        target_entry = tk.Entry(root, textvariable=self.target_value)
        target_entry.pack()
        
        # Bind the entry box to an update method
        self.target_value.trace_add("write", self.update_target_value)

        # Status label to show matches
        self.status = tk.Label(root, text="Status: Waiting for match...")
        self.status.pack()

        # Start the WebSocket listeners
        self.data_queue = asyncio.Queue()
        asyncio.create_task(self.start_websockets())
        asyncio.create_task(self.process_data())

    def update_target_value(self, *args):
        """Update the current target for comparison when the UI value changes."""
        try:
            self.current_target = float(self.target_value.get())  # convert to float for precision comparison
            self.status.config(text=f"Target value updated to: {self.current_target}")
        except ValueError:
            self.status.config(text="Invalid target input; please enter a number.")

    async def start_websockets(self):
        """Start the WebSocket clients to listen to both exchanges."""
        self.exchange1 = WebSocketClient(EXCHANGE_1_URL)
        self.exchange2 = WebSocketClient(EXCHANGE_2_URL)

        await asyncio.gather(
            self.exchange1.listen_to_data(self.data_queue),
            self.exchange2.listen_to_data(self.data_queue),
        )

    async def process_data(self):
        """Continuously processes data from both exchanges and checks against target value."""
        while True:
            url, data = await self.data_queue.get()

            # Attempt to parse WebSocket data to float for precision comparison
            try:
                data_value = float(data)
                if self.current_target is not None and data_value == self.current_target:
                    self.status.config(text=f"Match found on {url}! Executing order.")
                    # Insert order execution code here
                else:
                    self.status.config(text=f"No match found. Current data: {data_value}")
            except ValueError:
                print("Received non-numeric data from WebSocket.")

    def start(self):
        """Run the tkinter main loop."""
        self.root.mainloop()


async def main():
    # Create the main application window
    root = tk.Tk()
    app = TradingApp(root)

    # Run the Tkinter mainloop in a separate thread
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, app.start)

# Run the async main function
asyncio.run(main())
