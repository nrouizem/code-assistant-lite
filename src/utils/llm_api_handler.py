import config
import json
from copy import deepcopy

# --- LAZY INIT SETUP ---
_clients = {}

def _get_openai_client():
    """Initializes and returns an OpenAI client, caching it for future use."""
    if "openai" not in _clients:
        if not config.OPENAI_API_KEY:
            raise ValueError("Cannot use OpenAI model: OPENAI_API_KEY is not set.")
        from openai import OpenAI
        _clients["openai"] = OpenAI(api_key=config.OPENAI_API_KEY)
    return _clients["openai"]

def _get_gemini_client():
    """Initializes and returns a Gemini client module, caching it for future use."""
    if "gemini" not in _clients:
        if not config.GOOGLE_API_KEY:
            raise ValueError("Cannot use Gemini model: GOOGLE_API_KEY is not set.")
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GOOGLE_API_KEY)
            _clients["gemini"] = genai
        except ImportError:
            # Return None if the library isn't installed
            _clients["gemini"] = None
    return _clients["gemini"]

def _convert_to_gemini_format(messages: list[dict]) -> list[dict]:
    """Converts an OpenAI-formatted message list to Gemini's format."""
    gemini_contents = []
    system_prompt = ""
    # Extract the first system prompt, if it exists
    for i, msg in enumerate(messages):
        if msg.get("role") == "system":
            system_prompt = msg.get("content", "")
            messages = messages[i+1:] # Remove the system prompt from the list
            break

    # Add the system prompt to the start of the first user message
    if system_prompt and messages and messages[0].get("role") == "user":
        messages[0]['content'] = f"{system_prompt}\n\n{messages[0]['content']}"

    for message in messages:
        # Intentionally skipping stray system messages
        if message.get("role") == "system":
            continue
        
        gemini_contents.append({
            "role": "model" if message.get("role") == "assistant" else "user",
            "parts": [{"text": message.get("content", "")}]
        })
    return gemini_contents

def call_llm_with_fallback(messages: list[dict], model: str, fallback_model: str = None) -> dict:
    """
    Calls the LLM API with a primary model and attempts to use a fallback model
    if the primary call fails with a transient error.

    Returns a dictionary envelope with the result.
    """
    primary_result = _call_llm_api_once(messages, model)
    
    # If the primary call was successful or had a fatal error, return its result immediately
    if primary_result["status"] == "success" or primary_result["error_type"] == "fatal":
        return primary_result
        
    # If we are here, a non-fatal error occurred. Try the fallback instead
    if fallback_model:
        print(f"Warning: Model '{model}' failed with error: {primary_result['error_message']}. Attempting fallback to '{fallback_model}'.")
        fallback_result = _call_llm_api_once(messages, fallback_model)
        return fallback_result
    
    # If no fallback is available, return the original error.
    return primary_result

def _call_llm_api_once(messages: list[dict], model: str) -> dict:
    """
    Gets a completion from the specified model and returns a typed envelope.
    This internal function is called by the fallback wrapper.
    """
    if 'gpt' in model.lower():
        try:
            client = _get_openai_client()
            response = client.chat.completions.create(model=model, messages=messages)
            content = response.choices[0].message.content
            return {"status": "success", "content": content, "error_message": None, "error_type": None}
        except Exception as e:
            # Classify general API errors as 'transient' to allow for fallbacks/retries
            return {"status": "error", "content": None, "error_message": str(e), "error_type": "transient"}
    
    elif 'gemini' in model.lower():
        try:
            genai = _get_gemini_client()
            if genai is None:
                return {"status": "error", "content": None, "error_message": "Gemini library not installed.", "error_type": "fatal"}

            gemini_model = genai.GenerativeModel(model)
            response = gemini_model.generate_content(_convert_to_gemini_format(deepcopy(messages)))

            if response.candidates and response.candidates[0].finish_reason.name == "MAX_TOKENS":
                msg = f"Response from Gemini model {model} was truncated due to max token limit."
                return {"status": "error", "content": None, "error_message": msg, "error_type": "token_limit"}
            
            if response.candidates and response.candidates[0].finish_reason.name == "SAFETY":
                msg = f"Response from Gemini model {model} was blocked due to safety settings."
                return {"status": "error", "content": None, "error_message": msg, "error_type": "safety"}

            return {"status": "success", "content": response.text, "error_message": None, "error_type": None}
        except Exception as e:
            return {"status": "error", "content": None, "error_message": str(e), "error_type": "transient"}
    
    else:
        msg = f"Model provider for '{model}' not recognized."
        return {"status": "error", "content": None, "error_message": msg, "error_type": "fatal"}
