import subprocess
import time
import os
import sys

def run_bot(name, script):
    print(f"Starting {name}...")
    with open(f"{name}_logs.txt", "w") as log:
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd()
        )
    print(f"{name} started with PID: {process.pid}")
    return process

if __name__ == "__main__":
    os.chdir("/opt/render/project/src")
    
    # Start both bots
    hela = run_bot("hela", "Hela1.py")
    elsa = run_bot("elsa", "Elsa.py")
    
    # Wait for them
    hela.wait()
    elsa.wait()
