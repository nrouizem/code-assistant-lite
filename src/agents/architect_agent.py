import os
from .base_agent import BaseAgent
from src.utils.llm_api_handler import call_llm_with_fallback

class ArchitectAgent(BaseAgent):
    """
    An agent specializing in high-level software architecture analysis.
    Can be configured with a specific model and persona.
    """
    def __init__(self, model: str, system_prompt: str):
        self.model = model
        self.system_prompt = system_prompt

    def _create_prompt(self, codebase_content: str, user_prompt: str) -> list[dict]:
        """Creates the full prompt structure for the LLM API call."""
        
        user_prompt = f"""
        Here is some information directly from the client about this project:
        ---
        {user_prompt}
        
        ---
        Here is the codebase to review:
        ---
        {codebase_content}
        """
        
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def get_completion(self, prompt, model):
        result = call_llm_with_fallback(prompt, model=model, fallback_model="gpt-5")
        if result["status"] == "success":
            return result["content"]
        
        else:
            raise ValueError(f"LLM call failed for Architect: {result['error_message']}")

    def execute(self, codebase_content: str, user_prompt: str) -> str:
        """
        Executes the architectural analysis.
        """
        prompt = self._create_prompt(codebase_content, user_prompt)
        
        print(f"ArchitectAgent ({self.model}): Requesting analysis from LLM...")
        
        analysis = self.get_completion(prompt, self.model)
        
        return analysis