# --- FULL REPLACEMENT FOR: src/orchestration/debate_manager.py ---

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from src.agents.architect_agent import ArchitectAgent
import json
from src.utils.output_guardian import get_guarded_json
from src.utils.exceptions import UnparseableResponseError
from src.schemas.agent_responses import ArchitectRevision

class DebateManager:
    """
    Manages the debate loop for N ArchitectAgents.
    """
    def __init__(self, agents: list[ArchitectAgent]):
        self.agents = agents
        self.revision_prompt_template = self._load_prompt("src/prompts/agent_prompts/architect_revision.md")

    def _load_prompt(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def run_revision_for_agent(self, agent_index: int, all_analyses: list[str], user_prompt: str, critique_override: str = None, creative_sparks_json: str = None) -> tuple[str, int]:
  
        agent_revising = self.agents[agent_index]
        original_analysis = all_analyses[agent_index]
        creative_sparks_section = ""
        if creative_sparks_json:
            try:
                sparks = json.loads(creative_sparks_json)
                analogies = sparks.get("analogies", [])
                abstractions = sparks.get("abstractions", [])
                
                spark_details = []
                if analogies:
                    analogy_list = "\n".join([f"- {a}" for a in analogies])
                    spark_details.append(f"**Analogies from other domains:**\n{analogy_list}")
                
                if abstractions:
                    abstraction_list = "\n".join([f"- {a}" for a in abstractions])
                    spark_details.append(f"**Problem Abstractions:**\n{abstraction_list}")
                
                if spark_details:
                    creative_sparks_section = "\n\n".join(spark_details)

            except json.JSONDecodeError:
                creative_sparks_section = "Note: Creative sparks were provided but could not be parsed."

        if critique_override:
            critique_section = critique_override
        else:
            peer_critiques = []
            for i, analysis in enumerate(all_analyses):
                if i != agent_index:
                    peer_critiques.append(f"--- Peer {i+1}'s Analysis ---\n{analysis}")
            critique_section = "\n\n".join(peer_critiques)

        prompt = self.revision_prompt_template.format(
            original_analysis=original_analysis,
            user_prompt=user_prompt,
            critique=critique_section,
            creative_sparks=creative_sparks_section
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            revision_data = get_guarded_json(
                messages=messages,
                model=agent_revising.model,
                json_schema=ArchitectRevision
            )
            return revision_data.analysis_text, revision_data.confidence_score

        except UnparseableResponseError as e:
            print(f"Warning: Could not parse JSON for model {agent_revising.model}. Salvaging raw output.")
            salvaged_data = ArchitectRevision(
                analysis_text=f"--- PARSE_ERROR: The following is raw, un-parsed model output ---\n\n{e.raw_response}",
                confidence_score=1
            )
            return salvaged_data.analysis_text, salvaged_data.confidence_score


    def run_debate(self, initial_analyses: list[str], user_prompt: str, creative_sparks_json: str = None) -> list[tuple[int, str, int]]:
        """
        Orchestrates the full debate and revision cycle in parallel.
        Returns a list of tuples: (agent_index, revised_text, confidence_score)
        """
        print(f"Starting parallel revision round for {len(self.agents)} agents...")

        revised_results = []
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            future_to_agent_index = {
                executor.submit(
                    self.run_revision_for_agent,
                    agent_index,
                    all_analyses=initial_analyses,
                    user_prompt=user_prompt,
                    creative_sparks_json=creative_sparks_json
                ): agent_index
                for agent_index in range(len(self.agents))
            }

            for future in as_completed(future_to_agent_index):
                agent_index = future_to_agent_index[future]
                agent_model = self.agents[agent_index].model
                
                try:
                    text, score = future.result()
                    # Append the agent_index to the result tuple
                    revised_results.append((agent_index, text, score))
                    print(f"Agent {agent_index+1} ({agent_model}) completed revision successfully.")
                except Exception as exc:
                    print(f"!! Agent {agent_index+1} ({agent_model}) generated an exception during revision: {exc}")
        
        return revised_results