import os
from .base_agent import BaseAgent
from src.utils.llm_api_handler import call_llm_with_fallback

class ProjectManagerAgent(BaseAgent):
    """
    An agent that first generates clarifying questions, and then synthesizes
    the user's answers into a clear objective.
    """
    def __init__(self):
        # Load different prompts based on the mode
        self.audit_question_prompt = self._load_prompt("src/prompts/agent_prompts/pm_audit_questions.md")
        self.design_question_prompt = self._load_prompt("src/prompts/agent_prompts/pm_design_questions.md")
        self.objective_synth_prompt = self._load_prompt("src/prompts/agent_prompts/pm_synthesize_objective.md")

    def _load_prompt(self, path: str) -> str:
        # Helper to ensure file exists
        if not os.path.exists(path):
            # Fallback or error
            # For now, assume a default exists if a specific one is missing
            default_path = "src/prompts/agent_prompts/project_manager.md"
            print(f"Warning: Prompt not found at {path}. Using default.")
            with open(default_path, 'r', encoding='utf-8') as f:
                return f.read()
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_questions(self, codebase_content: str, mode: str) -> str:
        """
        Generates clarifying questions based on the codebase and the selected mode.
        """
        print("MGR: Project Manager is analyzing the codebase to generate clarifying questions...")
        
        # Mode-based prompt selection
        prompt_template = self.design_question_prompt if mode == 'design' else self.audit_question_prompt
        
        full_prompt = prompt_template.format(codebase=codebase_content)
        messages = [{"role": "user", "content": full_prompt}]
        result = call_llm_with_fallback(messages, model="gemini-2.5-pro", fallback_model="gpt-5")
        if result["status"] == "success":
            questions = result["content"]
            return questions
        
        else:
            raise ValueError(f"LLM call failed for PM's question generation: {result['error_message']}")

    def synthesize_objective(self, questions: str, answers: str, codebase_content: str) -> str:
        """
        Synthesizes the Q&A into a single objective paragraph.
        """
        print("MGR: Project Manager is synthesizing the objective...")
        full_prompt = self.objective_synth_prompt.format(
            questions=questions,
            answers=answers,
            codebase=codebase_content
        )
        messages = [{"role": "user", "content": full_prompt}]
        result = call_llm_with_fallback(messages, model="gemini-2.5-pro", fallback_model="gpt-5")
        if result["status"] == "success":
            objective = result["content"]
            return objective
        
        else:
            raise ValueError(f"LLM call failed for objective synthesis: {result['error_message']}")

    def execute(self, *args, **kwargs):
        pass