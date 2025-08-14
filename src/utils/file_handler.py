import os

def read_codebase(path: str) -> str:
    """
    Reads all files in a directory and concatenates them into a single string
    with file path headers, ignoring specified directories and file types.
    """
    full_code = []
    
    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'dist', 'build', 'runs', 'outputs'}
    ignore_extensions = {'.pyc', '.jsonl', '.lock', '.log', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico'}
    ignore_files = {}

    for root, dirs, files in os.walk(path, topdown=True):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            file_path = os.path.join(root, file)
            
            # Check for ignore conditions
            if file in ignore_files:
                continue
            if os.path.splitext(file)[1] in ignore_extensions:
                continue
            if file.startswith('.env'): # Catches .env, .env.local, etc.
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    relative_path = os.path.relpath(file_path, path)
                    full_code.append(f"--- START FILE: {relative_path} ---\n")
                    full_code.append(f.read())
                    full_code.append(f"\n--- END FILE: {relative_path} ---\n\n")
            except Exception as e:
                print(f"Could not read file {file_path}: {e}")
    
    return "".join(full_code)