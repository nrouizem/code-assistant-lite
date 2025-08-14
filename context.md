# System Knowledge & Ground Truth (August 2025)

This document contains facts that override the model's internal knowledge.

### 1
gpt-5, gpt-5-mini, and gpt-5-nano are valid OpenAI models.

### 2
The following is a correct way to call a Gemini model:

```python
import google.generativeai as genai
genai.configure(api_key=config.GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(model_name) # `model_name` is one of "gemini-2.5-pro" and "gemini-2.5-flash"
response = gemini_model.generate_content(messages)
```

