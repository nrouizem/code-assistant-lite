from json_repair import repair_json
import json
from pydantic import ValidationError
from .llm_api_handler import call_llm_with_fallback
from .exceptions import UnparseableResponseError

def get_guarded_json(messages: list[dict], model: str, json_schema):
    """
    Calls an LLM, asks for JSON, and attempts to repair and validate the output.

    Args:
        messages (list[dict]): The message list for the LLM call.
        model (str): The model identifier.
        json_schema (BaseModel): The Pydantic model to validate against.

    Returns:
        A validated Pydantic object.

    Raises:
        UnparseableResponseError: If the output cannot be parsed or validated.
    """
    # Layer 1: Ask the provider for JSON mode if it's OpenAI
    if 'gpt' in model.lower():
        # This is a simplification. A full Provider Adapter pattern would be more robust.
        # Note: The underlying call_llm_api needs to be updated to handle this parameter.
        # For now, we assume it's handled or we proceed to repair.
        pass

    result = call_llm_with_fallback(messages, model=model, fallback_model="gpt-5")
    if result["status"] != "success":
        raise ValueError(f"LLM call failed for get_guarded_json: {result['error_message']}")
    
    raw_response = result["content"]

    # Layer 2: Deterministic Extraction and Repair
    try:
        # Try to load it directly
        parsed_json = json.loads(raw_response)
    except json.JSONDecodeError:
        try:
            # If that fails, try to repair it
            repaired_json_str = repair_json(raw_response)
            parsed_json = json.loads(repaired_json_str)
        except (json.JSONDecodeError, ValueError) as e:
            # If both direct parsing and repair fail, raise custom error
            raise UnparseableResponseError(raw_response=raw_response)

    if isinstance(parsed_json, list):
        # If the LLM returned a list with a single object inside, extract it.
        if len(parsed_json) > 0 and isinstance(parsed_json[0], dict):
            print("Warning: LLM returned a list containing an object. Extracting first element.")
            parsed_json = parsed_json[0]
        else:
            # If it's a list but not in the expected format, it's unrecoverable.
            raise UnparseableResponseError(
                message="LLM returned a list that could not be interpreted as a single object.",
                raw_response=raw_response
            )

    # Finally, validate the successfully parsed JSON against the Pydantic schema
    try:
        validated_data = json_schema(**parsed_json)
        return validated_data
    except ValidationError as e:
        raise UnparseableResponseError(
            message=f"JSON was valid but failed schema validation: {e}",
            raw_response=raw_response
        )
