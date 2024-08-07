#Install before running
# pip install --upgrade google-cloud-aiplatform
# pip install -q -U google-generativeai

import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

def validate_name_gemini(name_to_validate, docai_extracted_name):
    model = GenerativeModel("gemini-1.0-pro-001")
    prompt = f"""Are these names: "{name_to_validate}" and "{docai_extracted_name}" considered the same? Only answer with 'true' if the full name is present in the piece of text, else output 'false'."""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.01
        }
    )

    if response.text == "true":
        print(f"Gemini Found Match! for {docai_extracted_name} and{name_to_validate}")
        return True
    else:
        print(f"No Match found for {docai_extracted_name} and {name_to_validate}")
        return False