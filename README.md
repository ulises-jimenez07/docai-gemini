# Document AI and Gemini
This repository contains a Python script that demonstrates how to use Google Cloud's Document AI and Gemini API to extract entities from a PDF document. 
The script compares the results from both APIs, highlighting the strengths and potential differences in their outputs.

Code sample leverages official documentation to send an [online processing request](https://cloud.google.com/document-ai/docs/samples/documentai-process-document), [batch processing request](https://cloud.google.com/document-ai/docs/samples/documentai-batch-process-document#documentai_batch_process_document-python) and [handle the  processing response](https://cloud.google.com/document-ai/docs/handle-response).

## Setup

1. **Install Dependencies:**
   ```bash
   pip install --upgrade google-cloud-aiplatform
   pip install -q -U google-generativeai
   pip install -r requirements.txt

2. **Assumption:**


This repository assumes, that this [codelab](https://www.cloudskillsboost.google/focuses/67855?parent=catalog) has been completed, that a dataset with the test documents is available and there exists a Document AI extractor.

Once it has been completed, additionally create two buckets, for batch processing, namely, temp and output.

```bash
TEMP_BUCKET_URI = f"gs://documentai-temp-{PROJECT_ID}-unique"

gsutil mb -l {LOCATION} -p {PROJECT_ID} {BUCKET_URI}

OUT_BUCKET_URI = f"gs://documentai-temp-{TEMP_BUCKET_URI}-unique"

gsutil mb -l {LOCATION} -p {PROJECT_ID} {OUT_BUCKET_URI}
```




# Code Overview
- `test_doc_ai.py`: This script orchestrates the entire process:

  - It first uses the Document AI API to process the PDF and extract entities.
  - Then, it utilizes the Gemini API with a tailored prompt to extract entities from the same PDF.
  - Finally, it compares the results from both APIs and prints a summary.
- `extractor.py`: Contains classes for interacting with the Document AI API for both online and batch processing.

- `entity_processor.py`: Defines classes for extracting entities from the Document AI output and the Gemini API response.

- `prompts_module.py`: Provides functions to generate prompts for entity extraction and comparison tasks for the Gemini API.

- `temp_file_uploader.py`: Handles uploading files to a temporary Google Cloud Storage location for processing.

# Notes
- Ensure that your Google Cloud project has the necessary APIs enabled (Document AI, Vertex AI, etc.).
- The script is configured to process a single PDF file. You can modify it to process multiple files or handle different input sources.
- The accuracy and performance of entity extraction may vary depending on the document complexity and the chosen API parameters.
- This script is intended for demonstration purposes. You can adapt and extend it to suit your specific use case and integrate it into your applications.