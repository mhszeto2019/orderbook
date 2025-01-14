from multiprocessing import Manager, Process
import random
import random
from multiprocessing import Manager, Process

class Apple:
    def __init__(self, shared_state):
        self.state = shared_state  # Shared dictionary to hold attributes
        self.state['num'] = 0  # Include 'num' in the shared state

    def set_color(self, new_color):
        self.state['color'] = new_color

    def get_color(self):
        return self.state['color']

    def running(self):
        """Simulate some work and update 'num'."""
        num = random.randint(0, 10)
        self.state['num'] = num  # Update shared state
        print(f"Running: Set num to {num}")


def run_apple(apple_instance):
    """Run the `Apple` instance's `running` method in a process."""
    apple_instance.running()

def change_color(shared_state, new_color):
    """Update the color in the shared state."""
    shared_state['color'] = new_color
    print(f"Color changed to {new_color}")
    
import time
if __name__ == "__main__":
    manager = Manager()
    shared_state = manager.dict({'color': 'red'})  # Initialize shared state with 'color'

    apple = Apple(shared_state)

    # Start the `Apple` instance in a separate process
    process = Process(target=apple.running)
    process.start()

    try:
        # Change the color while the process is running
        time.sleep(2)
        change_color(shared_state, 'blue')  # Change color to blue

        time.sleep(2)
        change_color(shared_state, 'green')  # Change color to green

        time.sleep(2)
        change_color(shared_state, 'yellow')  # Change color to yellow

    except KeyboardInterrupt:
        print("Stopping the process...")
    finally:
        process.terminate()  # Terminate the process
        process.join()