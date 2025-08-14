import sys
import argparse
from src.utils.file_handler import read_codebase
from src.orchestration.analysis_flow import run_multi_agent_analysis, run_design_mode_analysis
from src.agents.project_manager_agent import ProjectManagerAgent

def main():
    # Use argparse for robust command-line argument handling
    parser = argparse.ArgumentParser(
        description="A multi-agent AI code assistant.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "codebase_path", 
        type=str, 
        help="The path to the codebase to analyze."
    )
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=['audit', 'design'], 
        default='audit', 
        help="The mode of operation:\n"
             "audit  - (Default) Perform a detailed code review to find bugs and flaws.\n"
             "design - Brainstorm novel features and high-level architectural improvements."
    )
    
    args = parser.parse_args()

    # --- Step 1: Select the initial prompt based on the chosen mode ---
    if args.mode == 'design':
        try:
            with open("src/prompts/user_prompts/design_mode_prompt.md", 'r') as f:
                initial_user_prompt = f.read()
            print("Running in DESIGN mode.")
        except FileNotFoundError:
            print("Error: design_mode_prompt.txt not found. Please create it in src/prompts/user_prompts/")
            sys.exit(1)
    else: # Default to audit mode
        initial_user_prompt = "Please act as a senior software architect and provide a high-level conceptual review of my codebase."
        print("Running in AUDIT mode.")

    codebase_path = args.codebase_path
    print(f"Initializing analysis for: {codebase_path}")
    code_content = read_codebase(codebase_path)

    # --- Step 2: Generate and Ask Clarifying Questions ---
    # TODO: ask different questions for each mode
    project_manager = ProjectManagerAgent()
    clarifying_questions = project_manager.generate_questions(code_content, mode=args.mode)

    print("\n--- Please Answer the Following Questions to Focus the Analysis ---")
    print(clarifying_questions)
    
    print("--------------------------------------------------------------------")
    print("Please provide your answers below (type 'DONE' on a new line when finished):")
    
    user_answers = []
    while True:
        line = input()
        if line.upper() == 'DONE':
            break
        user_answers.append(line)
    
    answers_str = "\n".join(user_answers)

    # --- Step 3: Synthesize the Objective ---
    objective = project_manager.synthesize_objective(clarifying_questions, answers_str, code_content)
    print("\nSynthesized Objective:\n" + objective)

    # --- Step 4: Run the Full Analysis ---
    focused_user_prompt = f"""
    **Initial User Request:**
    {initial_user_prompt}

    **Synthesized Project Objective (from user Q&A):**
    {objective}

    Please provide a comprehensive analysis that fulfills the initial request, guided by the synthesized objective.
    """

    print("\nThank you. Starting full multi-agent analysis with the focused objective...")
    
    if args.mode == 'design':
        final_report = run_design_mode_analysis(code_content, focused_user_prompt)
    else:
        final_report = run_multi_agent_analysis(code_content, focused_user_prompt)

    print("\n--- FINAL SYNTHESIZED REPORT ---")
    print(final_report)
    print("--------------------------------\n")

if __name__ == "__main__":
    main()