from .base_agent import BaseAgent
from src.utils.llm_api_handler import call_llm_with_fallback
from src.schemas.events import Event
from typing import List
import json

class SynthesizerAgent(BaseAgent):
    def __init__(self, prompt_path="src/prompts/agent_prompts/synthesizer.md"):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

    def execute(self, user_prompt: str, events: List[Event]) -> str:
        """
        Executes the synthesis task using the full reasoning ledger.

        Args:
            user_prompt: The user's synthesized objective.
            events: A list of all Event objects from the current run.
        """
        
        try:
            events_as_dicts = [event.model_dump() for event in events]
            all_events_formatted = json.dumps(events_as_dicts, indent=2, default=str)
        except TypeError as e:
            print(f"Error serializing events to JSON: {e}")
            all_events_formatted = "Error: Could not format the event log."


        full_prompt = self.prompt_template.format(
            user_prompt=user_prompt, 
            all_events=all_events_formatted
        )

        messages = [{"role": "user", "content": full_prompt}]

        print("SynthesizerAgent: Combining reports into a final architectural plan...")
        result = call_llm_with_fallback(messages, model="gpt-5", fallback_model="gemini-2.5-pro")

        if result["status"] == "success":
            synthesis = result["content"]
            return synthesis
        
        else:
            raise ValueError(f"LLM call failed for synthesis: {result['error_message']}")