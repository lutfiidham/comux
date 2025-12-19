#!/usr/bin/env python3
"""Debug script to test spinner in Termux."""

import time
import itertools
import sys

class SimpleSpinner:
    def __init__(self, message="Thinking"):
        self.message = message
        self.running = False
        self.spinner = itertools.cycle(['|', '/', '-', '\\'])

    def start(self):
        self.running = True
        import threading
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        time.sleep(0.2)
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()

    def _animate(self):
        time.sleep(0.1)
        while self.running:
            sys.stdout.write(f'\r{self.message} {next(self.spinner)}')
            sys.stdout.flush()
            time.sleep(0.2)

def test():
    print("Testing spinner...")
    print("Type something and press enter:")
    user_input = input(">>> ")

    spinner = SimpleSpinner("Processing")
    spinner.start()

    # Simulate work
    time.sleep(3)

    spinner.stop()
    print(f"You typed: {user_input}")

if __name__ == "__main__":
    test()