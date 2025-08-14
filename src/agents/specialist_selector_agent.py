import os
from .base_agent import BaseAgent
from src.utils.llm_api_handler import call_llm_with_fallback

class SpecialistSelectorAgent(BaseAgent):
    """
    An agent that dynamically discovers and selects the most appropriate specialist.
    """
    PROMPTS_DIR = "src/prompts/specialist_prompts/"

    @staticmethod
    def _generate_specialist_mapping():
        """
        Scans the prompts directory to dynamically create the specialist allowlist.
        The role name is derived from the filename (e.g., 'web_security_specialist.md' -> 'web_security_specialist').
        """
        if not os.path.isdir(SpecialistSelectorAgent.PROMPTS_DIR):
            print(f"Warning: Specialist prompts directory not found at '{SpecialistSelectorAgent.PROMPTS_DIR}'")
            return {}
        
        mapping = {}
        for filename in os.listdir(SpecialistSelectorAgent.PROMPTS_DIR):
            if filename.endswith(".md"):
                # The role is the filename without the extension.
                role_name = filename[:-3] # Removes .md
                full_path = os.path.join(SpecialistSelectorAgent.PROMPTS_DIR, filename)
                mapping[role_name] = full_path
        return mapping

    def __init__(self, prompt_path="src/prompts/agent_prompts/specialist_selector.md"):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
        self.SPECIALIST_MAPPING = self._generate_specialist_mapping()

    def execute(self, codebase_content: str, user_prompt: str) -> str:
        """
        Selects a specialist based on the codebase.
        Returns a validated specialist role name from the dynamically generated allowlist.
        """
        if not self.SPECIALIST_MAPPING:
            print("Error: No specialist prompts found. Cannot perform selection.")
            return "default_specialist" # A safe fallback

        specialist_choices = "\n- ".join(self.SPECIALIST_MAPPING.keys())
        
        full_prompt = self.prompt_template.format(
            codebase=codebase_content, 
            user_prompt=user_prompt,
            specialist_choices=specialist_choices
        )
        
        messages = [{"role": "user", "content": full_prompt}]
        result = call_llm_with_fallback(messages, model="gemini-2.5-flash", fallback_model="gpt-5-mini")

        if result["status"] == "success":
            cleaned_output = result["content"].strip().lower()
            if not cleaned_output.endswith("_specialist"):
                cleaned_output += "_specialist"

            if cleaned_output in self.SPECIALIST_MAPPING:
                return cleaned_output
            else:
                raise ValueError(f"LLM returned an invalid specialist role: '{cleaned_output}'. Valid roles are: {list(self.SPECIALIST_MAPPING.keys())}")
        
        else:
            print(f"ERROR: LLM call failed: {result['error_message']}")
            raise ValueError(f"LLM call failed for specialist selection: {result['error_message']}")