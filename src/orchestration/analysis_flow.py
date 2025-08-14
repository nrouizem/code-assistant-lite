from src.agents.architect_agent import ArchitectAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.agents.devils_advocate_agent import DevilsAdvocateAgent
from src.agents.qa_agent import QAAgent
from .debate_manager import DebateManager
from src.agents.project_manager_agent import ProjectManagerAgent
from src.agents.specialist_selector_agent import SpecialistSelectorAgent
from src.agents.analogy_abstraction_agent import AnalogyAbstractionAgent
from src.utils.exceptions import UnparseableResponseError
from src.schemas.agent_responses import AnalogyAbstractions
import uuid
from .reasoning_ledger import ReasoningLedger
from src.schemas.events import (
    Event, 
    INITIAL_ANALYSIS_PRODUCED, 
    REVISION_COMPLETE, 
    DEVILS_ADVOCATE_CRITIQUE_PRODUCED,
    CREATIVE_SPARKS_PRODUCED
)

from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed


def _run_agent_execution(agent, codebase_content, user_prompt):
    """Helper function to execute an agent's task for parallel execution."""
    return agent.execute(codebase_content, user_prompt)

def run_multi_agent_analysis(codebase_content: str, user_prompt: str) -> str:
    """
    Orchestrates N agents through the full analysis pipeline, including a
    final revision stage after the Devil's Advocate critique.
    """
    run_id = str(uuid.uuid4())
    ledger = ReasoningLedger(run_id=run_id)
    print(f"--- Starting new AUDIT run, ID: {run_id} ---")

    print("--- [Stage 1/7] Selecting Specialist ---")
    specialist_selector = SpecialistSelectorAgent()
    try:
        specialist_role = specialist_selector.execute(codebase_content, user_prompt)
        print(f" MGR: Specialist selected: {specialist_role}")
    except (ValueError, EnvironmentError) as e:
        print(f"\nFATAL ERROR in specialist selection: {e}")
        print("Aborting analysis.")
        return f"CRITICAL_FAILURE: {e}"

    # --- Agent Initialization ---
    try:
        prompt_path = f"src/prompts/specialist_prompts/{specialist_role}.md"
        with open(prompt_path, 'r') as f:
            specialist_prompt = f.read()
    except FileNotFoundError:
        print(f" MGR: Warning - Specialist prompt for '{specialist_role}' not found. Using default.")
        with open("src/prompts/specialist_prompts/default_specialist.md", 'r') as f:
            specialist_prompt = f.read()

    high_level_prompt = """
        You are a world-class technology strategist, similar to a consultant at McKinsey or BCG, known for your ability to see the "big picture." Your focus is not on code-level details but on the overall strategic approach.
        Analyze the provided codebase and its objective. Your task is to provide a high-level overview, answering the following key questions:

        1. Core Strategy: What is the fundamental approach this codebase takes to solve the problem?
        2. Key Ideas: What are the 1-3 core, innovative ideas or mechanisms at the heart of this system?
        3. Missing Big Ideas: What major strategic opportunities or alternative approaches are being missed? Are there any "game-changing" concepts from other domains that could be applied here?

        Please keep your analysis conceptual and strategic. Avoid mentioning specific functions, variable names, or minor implementation details.
        """

    architects = [
        ArchitectAgent(model="gemini-2.5-pro", system_prompt="You are an innovative architect focused on creative solutions and scalability."),
        ArchitectAgent(model="gemini-2.5-pro", system_prompt=high_level_prompt),
        ArchitectAgent(model="gpt-5", system_prompt=specialist_prompt),
    ]
    print(f"Initializing analysis with a team of {len(architects)} architects.")

    # --- Stage 2: Independent Analysis (v1) ---
    print("--- [Stage 2/7] Running Independent Analyses ---")
    initial_analyses_text = []
    with ThreadPoolExecutor(max_workers=len(architects)) as executor:
        future_to_agent = {
            executor.submit(_run_agent_execution, agent, codebase_content, user_prompt): agent
            for agent in architects
        }
        for future in as_completed(future_to_agent):
            agent = future_to_agent[future]
            try:
                result_text = future.result()
                initial_analyses_text.append(result_text) # Collect for debate
                event = Event(
                    run_id=run_id,
                    event_type=INITIAL_ANALYSIS_PRODUCED,
                    source=f"ArchitectAgent:{agent.model}",
                    payload={"analysis_text": result_text}
                )
                ledger.log(event)
                print(f"Agent ({agent.model}) completed initial analysis and logged to ledger.")
            except Exception as exc:
                print(f"!! Agent ({agent.model}) generated an exception during initial analysis: {exc}")

    # --- Stage 3: Collaborative Debate & Revision (v2) ---
    print("\n--- [Stage 3/7] Starting Collaborative Debate ---")
    debate_manager = DebateManager(architects)
    # The debate returns the index for logging
    analyses_v2_results = debate_manager.run_debate(initial_analyses_text, user_prompt)
    
    analyses_v2_text = [text for _, text, _ in analyses_v2_results] # Keep a list of just the text for the devil's advocate
    
    # Log the revised analyses correctly
    for agent_index, text, score in analyses_v2_results:
        agent = architects[agent_index]
        event = Event(
            run_id=run_id,
            event_type=REVISION_COMPLETE,
            source=f"ArchitectAgent:{agent.model}",
            payload={"analysis_text": text, "confidence_score": score, "revision_stage": "initial_debate"}
        )
        ledger.log(event)

    # --- Stage 4: Devil's Advocate Review ---
    print("\n--- [Stage 4/7] Running Devil's Advocate Review ---")
    with open("context.md", 'r') as f:
        ground_truth_context = f.read()
    devil = DevilsAdvocateAgent()
    critique = devil.execute(analyses_v2_text, codebase_content, user_prompt, ground_truth_context)
    critique_event = Event(
        run_id=run_id,
        event_type=DEVILS_ADVOCATE_CRITIQUE_PRODUCED,
        source="DevilsAdvocateAgent",
        payload={"critique_text": critique}
    )
    ledger.log(critique_event)
    print("\nDEVIL'S ADVOCATE CRITIQUE:\n" + critique)

    # --- Stage 5: Final Revisions based on Red Team Feedback (v3) ---
    print("\n--- [Stage 5/7] Performing Final Revisions Post-Critique ---")
    with ThreadPoolExecutor(max_workers=len(architects)) as executor:
        future_to_agent_index = {
            executor.submit(
                debate_manager.run_revision_for_agent,
                agent_index,
                all_analyses=analyses_v2_text,
                user_prompt=user_prompt,
                critique_override=critique
            ): agent_index
            for agent_index in range(len(architects))
        }
        for future in as_completed(future_to_agent_index):
            agent_index = future_to_agent_index[future]
            agent_model = architects[agent_index].model
            try:
                text, score = future.result()
                # LOG THE FINAL REVISION
                event = Event(
                    run_id=run_id,
                    event_type=REVISION_COMPLETE,
                    source=f"ArchitectAgent:{agent_model}",
                    payload={"analysis_text": text, "confidence_score": score, "revision_stage": "final"}
                )
                ledger.log(event)
                print(f"Agent {agent_index+1} ({agent_model}) completed final revision.")
            except Exception as exc:
                print(f"!! Agent {agent_index+1} ({agent_model}) generated an exception during final revision: {exc}")
    
    # --- Stage 6: Synthesis ---
    print("\n--- [Stage 6/7] Synthesizing Final Report ---")
    synthesizer = SynthesizerAgent()
    # The synthesizer now gets the complete and correct ledger
    final_report_draft = synthesizer.execute(user_prompt, ledger.read_events())
    
    # --- Stage 7: QA Review ---
    print("\n--- [Stage 7/7] Running Quality Assurance Check ---")
    qa_agent = QAAgent()
    qa_feedback = qa_agent.execute(user_prompt, final_report_draft)

    if qa_feedback.strip().upper() == "APPROVED":
        print("Report APPROVED BY QA.")
        return final_report_draft
    else:
        print("Report needs revisions based on QA feedback:")
        print(qa_feedback)
        return f"--- DRAFT REPORT (Needs Revision) ---\n{final_report_draft}\n\n--- QA FEEDBACK ---\n{qa_feedback}"


def run_design_mode_analysis(codebase_content: str, user_prompt: str) -> str:
    """
    Orchestrates agents for high-level, creative architectural design.
    """
    run_id = str(uuid.uuid4())
    ledger = ReasoningLedger(run_id=run_id)
    print(f"--- Starting new DESIGN run, ID: {run_id} ---")

    architects = [
        ArchitectAgent(model="gpt-5", system_prompt="You are a visionary product designer focused on user experience and market disruption. Think outside the box."),
        ArchitectAgent(model="gemini-2.5-pro", system_prompt="You are a systems architect who thinks in terms of broad patterns and scalable, long-term structures. You draw inspiration from complex systems."),
        ArchitectAgent(model="gemini-2.5-pro", system_prompt="You are a pragmatic engineer who ensures that creative ideas are grounded in technical reality. You provide the 'how-to' for the 'what-if'.")
    ]
    aa_agent = AnalogyAbstractionAgent()
    debate_manager = DebateManager(architects)
    devil = DevilsAdvocateAgent()
    synthesizer = SynthesizerAgent()
    qa_agent = QAAgent()

    print(f"Initializing DESIGN MODE with a team of {len(architects)} architects and 1 creative catalyst.")

    # --- Stage 2: Independent Analysis ---
    print("\n--- [Stage 2/8] Running Independent Analyses ---")
    initial_analyses_text = []
    with ThreadPoolExecutor(max_workers=len(architects)) as executor:
        future_to_agent = {
            executor.submit(_run_agent_execution, agent, codebase_content, user_prompt): agent
            for agent in architects
        }
        for future in as_completed(future_to_agent):
            agent = future_to_agent[future]
            try:
                result_text = future.result()
                initial_analyses_text.append(result_text) # Collect for debate
                event = Event(
                    run_id=run_id,
                    event_type=INITIAL_ANALYSIS_PRODUCED,
                    source=f"ArchitectAgent:{agent.model}",
                    payload={"analysis_text": result_text}
                )
                ledger.log(event)
                print(f"Agent ({agent.model}) completed initial analysis and logged to ledger.")
            except Exception as exc:
                print(f"!! Agent ({agent.model}) generated an exception during initial analysis: {exc}")

    # --- Stage 3: Creative Catalyst ---
    print("\n--- [Stage 3/8] Running Analogy & Abstraction Agent ---")
    creative_sparks_json = None
    try:
        creative_sparks_data = aa_agent.execute(user_prompt, initial_analyses_text)
        event = Event(
            run_id=run_id,
            event_type=CREATIVE_SPARKS_PRODUCED,
            source="AnalogyAbstractionAgent",
            payload=creative_sparks_data.model_dump()
        )
        ledger.log(event)
        creative_sparks_json = creative_sparks_data.model_dump_json()
        print(f"A&A Agent Output logged to ledger.")
    except UnparseableResponseError as e:
        print(f"Warning: AnalogyAbstractionAgent failed to generate valid JSON. {e}")
        print("Proceeding with debate phase without creative sparks.")
        creative_sparks_json = AnalogyAbstractions().model_dump_json()

    # --- Stage 4: Collaborative Debate & Revision ---
    print("\n--- [Stage 4/8] Starting Collaborative Debate ---")
    # This returns (agent_index, text, score)
    analyses_v2_results = debate_manager.run_debate(
        initial_analyses=initial_analyses_text,
        user_prompt=user_prompt,
        creative_sparks_json=creative_sparks_json
    )
    
    analyses_v2_text = [text for _, text, _ in analyses_v2_results] # Keep a list of just the text for the devil

    for agent_index, text, score in analyses_v2_results:
        # Use the correct agent from the index for logging
        agent = architects[agent_index]
        event = Event(
            run_id=run_id,
            event_type=REVISION_COMPLETE,
            source=f"ArchitectAgent:{agent.model}",
            payload={"analysis_text": text, "confidence_score": score, "revision_stage": "initial_debate"}
        )
        ledger.log(event)

    # --- Stage 5: Devil's Advocate Review ---
    print("\n--- [Stage 5/8] Running Devil's Advocate Review ---")
    with open("context.md", 'r') as f:
        ground_truth_context = f.read()
    critique = devil.execute(analyses_v2_text, codebase_content, user_prompt, ground_truth_context)
    critique_event = Event(
        run_id=run_id,
        event_type=DEVILS_ADVOCATE_CRITIQUE_PRODUCED,
        source="DevilsAdvocateAgent",
        payload={"critique_text": critique}
    )
    ledger.log(critique_event)
    print("\nDEVIL'S ADVOCATE CRITIQUE:\n" + critique)

    # --- Stage 6: Final Revisions ---
    print("\n--- [Stage 6/8] Performing Final Revisions Post-Critique ---")
    with ThreadPoolExecutor(max_workers=len(architects)) as executor:
        future_to_agent_index = {
            executor.submit(
                debate_manager.run_revision_for_agent,
                agent_index,
                all_analyses=analyses_v2_text,
                user_prompt=user_prompt,
                critique_override=critique
            ): agent_index
            for agent_index in range(len(architects))
        }
        for future in as_completed(future_to_agent_index):
            agent_index = future_to_agent_index[future]
            agent = architects[agent_index]
            try:
                text, score = future.result()
                event = Event(
                    run_id=run_id,
                    event_type=REVISION_COMPLETE,
                    source=f"ArchitectAgent:{agent.model}",
                    payload={"analysis_text": text, "confidence_score": score, "revision_stage": "final"}
                )
                ledger.log(event)
                print(f"Agent {agent_index+1} ({agent.model}) completed final revision.")
            except Exception as exc:
                print(f"!! Agent {agent_index+1} ({agent.model}) generated an exception during final revision: {exc}")
    
    # --- Stage 7: Synthesis ---
    print("\n--- [Stage 7/8] Synthesizing Final Report ---")
    final_report_draft = synthesizer.execute(user_prompt, ledger.read_events())
    
    # --- Stage 8: QA Review ---
    print("\n--- [Stage 8/8] Running Quality Assurance Check ---")
    qa_feedback = qa_agent.execute(user_prompt, final_report_draft)

    if qa_feedback.strip().upper() == "APPROVED":
        print("Report APPROVED BY QA.")
        return final_report_draft
    else:
        print("Report needs revisions based on QA feedback:")
        print(qa_feedback)
        return f"--- DRAFT REPORT (Needs Revision) ---\n{final_report_draft}\n\n--- QA FEEDBACK ---\n{qa_feedback}"