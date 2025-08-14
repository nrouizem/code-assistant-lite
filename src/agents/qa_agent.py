from .base_agent import BaseAgent
from src.utils.llm_api_handler import call_llm_with_fallback

class QAAgent(BaseAgent):
    """
    An agent that performs a final quality assurance check on the report.
    """
    def __init__(self, prompt_path="src/prompts/agent_prompts/qa_review.md"):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

    def execute(self, user_prompt: str, final_report: str) -> str:
        """
        Executes the QA check.
        Returns 'APPROVED' or a list of revisions.
        """
        print("QA Agent: Performing final review...")
        
        full_prompt = self.prompt_template.format(
            user_prompt=user_prompt, 
            final_report=final_report
        )
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Relatively cheap model is fine for classification
        result = call_llm_with_fallback(messages, model="gpt-5-mini", fallback_model="gemini-2.5-flash")

        if result["status"] == "success":
            feedback = result["content"]
            return feedback
        
        else:
            raise ValueError(f"LLM call failed for QA Agent: {result['error_message']}")