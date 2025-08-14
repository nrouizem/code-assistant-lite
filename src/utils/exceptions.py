class UnparseableResponseError(Exception):
    """Custom exception raised when an LLM output cannot be parsed into the target schema."""
    def __init__(self, message="Failed to parse LLM response", raw_response=None):
        self.raw_response = raw_response
        super().__init__(f"{message}. Raw response: '{str(raw_response)[:100]}...'")
