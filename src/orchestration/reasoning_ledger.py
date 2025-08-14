import os
import json
from typing import List
from src.schemas.events import Event

class ReasoningLedger:
    """
    Manages the reading and writing of events to a run-specific ledger file.
    The ledger is stored as a JSON Lines (.jsonl) file, which is efficient
    for append-only logs.
    """
    def __init__(self, run_id: str, log_dir: str = "runs"):
        self.run_id = run_id
        self.run_dir = os.path.join(log_dir, run_id)
        self.ledger_path = os.path.join(self.run_dir, "reasoning_ledger.jsonl")
        
        # Ensure the directory for this run exists.
        os.makedirs(self.run_dir, exist_ok=True)

    def log(self, event: Event):
        """
        Appends a new event to the ledger file.

        Args:
            event: The Event object to log.
        """
        # Ensure the event's run_id matches the ledger's run_id.
        if event.run_id != self.run_id:
            raise ValueError("Event run_id does not match Ledger run_id.")
            
        # Append the JSON representation of the event as a new line.
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(event.model_dump_json() + "\n")

    def read_events(self) -> List[Event]:
        """
        Reads all events from the ledger file and returns them as a list.

        Returns:
            A list of Event objects.
        """
        if not os.path.exists(self.ledger_path):
            return []
        
        events = []
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        events.append(Event(**data))
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode line in ledger: {line}")
        return events