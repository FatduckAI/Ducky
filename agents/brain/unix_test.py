import os
import random
import subprocess
import time
from typing import Dict, List


class UnixSandbox:
    def __init__(self):
        self.filesystem = {"/": {}}
        self.current_directory = "/"
        self.environment_variables = {"PATH": "/bin:/usr/bin"}
        self.entry_script = "./entrypoint.sh"  # Path to your bash script

    def run_command(self, command: str) -> str:
        parts = command.split()
        script_command = parts[0]
        args = parts[1:]
        
        try:
            result = subprocess.run([self.entry_script, script_command] + args, 
                                    capture_output=True, text=True, check=True)
            return f"Output:\n{result.stdout}\nErrors:\n{result.stderr}"
        except subprocess.CalledProcessError as e:
            return f"Error running command: {e}\nOutput:\n{e.output}\nErrors:\n{e.stderr}"

class BrainAI:
    def __init__(self, sandbox: UnixSandbox):
        self.sandbox = sandbox

    def make_decision(self) -> str:
        actions = [
            "edgelord",
            "hitchiker",
            "dinner_with_andre",
            "narratives"
        ]
        return random.choice(actions)

    def run(self) -> str:
        decision = self.make_decision()
        return self.sandbox.run_command(decision)

def simulate_unix_sandbox(duration_minutes: int = 60, interval_minutes: int = 10):
    sandbox = UnixSandbox()
    brain = BrainAI(sandbox)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Brain AI activated:")
        result = brain.run()
        print(f"$ {result}")
        
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    simulate_unix_sandbox()