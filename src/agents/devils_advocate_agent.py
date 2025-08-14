from .base_agent import BaseAgent
from src.utils.llm_api_handler import call_llm_with_fallback

class DevilsAdvocateAgent(BaseAgent):
    def __init__(self, prompt_path="src/prompts/agent_prompts/devils_advocate.md"):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

    def execute(
            self,
            analyses: list[str],
            codebase_content: str,
            user_prompt: str,
            ground_truth_context: str) -> str:
        """
        Executes the critique on N analyses.
        Args:
            analyses: A list of the refined analysis strings.
            codebase_content: The full codebase content for context.
        Returns:
            A string containing the Devil's Advocate's critique.
        """
        print(f"Devil's Advocate: Searching for flaws in {len(analyses)} reports...")

        analyses_text_block = []
        for i, analysis in enumerate(analyses):
            header = f"--- Refined Analysis {i+1} ---"
            analyses_text_block.append(f"{header}\n{analysis}")

        all_analyses_formatted = "\n\n".join(analyses_text_block)

        full_prompt = self.prompt_template.format(
            all_analyses=all_analyses_formatted,
            codebase=codebase_content,
            user_prompt=user_prompt,
            ground_truth_context=ground_truth_context
        )

        messages = [{"role": "user", "content": full_prompt}]
        result = call_llm_with_fallback(messages, model="gemini-2.5-pro", fallback_model="gpt-5")
        if result["status"] == "success":
            critique = result["content"]
            return critique
        
        else:
            raise ValueError(f"LLM call failed for Devil's Advocate: {result['error_message']}")