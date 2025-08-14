import json
from .base_agent import BaseAgent
from src.utils.output_guardian import get_guarded_json
from src.schemas.agent_responses import AnalogyAbstractions

class AnalogyAbstractionAgent(BaseAgent):
    """
    An agent that injects divergent thinking into the design process by
    generating analogies and problem abstractions.
    """
    def __init__(self, prompt_path="src/prompts/agent_prompts/analogy_abstraction.md"):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

    def execute(self, user_prompt: str, initial_analyses: list[str]) -> str:
        """
        Generates creative analogies and abstractions based on the core problem.

        Args:
            user_prompt: The synthesized user objective.
            initial_analyses: The list of initial analyses from the ArchitectAgents.

        Returns:
            A JSON string containing 'analogies' and 'abstractions'.
        """
        print("A&A Agent: Generating creative sparks...")

        analyses_text_block = []
        for i, analysis in enumerate(initial_analyses):
            header = f"--- Initial Analysis from Architect {i+1} ---"
            analyses_text_block.append(f"{header}\n{analysis}")
        
        all_analyses_formatted = "\n\n".join(analyses_text_block)

        full_prompt = self.prompt_template.format(
            user_prompt=user_prompt,
            initial_analyses=all_analyses_formatted
        )
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Creative task gets a strong model
        creative_sparks_data = get_guarded_json(
            messages=messages,
            model="gpt-5",
            json_schema=AnalogyAbstractions
        )

        return creative_sparks_data