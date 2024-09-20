# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import os
import json
import re
import uuid

from typing import Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError
from google.cloud import documentai
from google.cloud import storage
from google.api_core.exceptions import NotFound


from extractor import BatchDocumentExtractor
from extractor import OnlineDocumentExtractor

from entity_processor import DocumentAIEntityExtractor, ModelBasedEntityExtractor

from prompts_module import get_extract_entities_prompt, get_compare_entities_prompt
from temp_file_uploader import TempFileUploader

# Batch processing


import vertexai
from vertexai.generative_models import GenerativeModel, Part


PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION")
MODEL_NAME = "gemini-1.5-flash-001"
LOCATION = REGION.split("-")[0]
PROCESSOR_ID = os.getenv("PROCESSOR_ID")
PROCESSOR_VERSION_ID = os.getenv("PROCESSOR_VERSION_ID")
TEMP_BUCKET = os.getenv("TEMP_BUCKET")
OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET")
FIREBASE_DB = os.getenv("FIREBASE_DB")


vertexai.init(project=PROJECT_ID, location=REGION)
storage_client = storage.Client(project=PROJECT_ID)

from firebase_admin import db, initialize_app
from firebase_functions import https_fn
from google.cloud import firestore

initialize_app()
app = flask.Flask(__name__)
db = firestore.Client(project=PROJECT_ID, database=FIREBASE_DB)


def on_document_added(event, context):
    pubsub_message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    src_bucket = pubsub_message["bucket"]
    src_fname = pubsub_message["name"]
    mime_type = pubsub_message["contentType"]

    file_path = download_storage_tmp(src_bucket, src_fname)

    online_extractor = OnlineDocumentExtractor(
        project_id=PROJECT_ID,
        location=LOCATION,
        processor_id=PROCESSOR_ID,
        processor_version_id=PROCESSOR_VERSION_ID,
    )
    online_document = online_extractor.process_document(file_path, mime_type)

    # 1. Using DocumentAIEntityExtractor
    docai_entity_extractor = DocumentAIEntityExtractor(online_document)
    docai_entities = docai_entity_extractor.extract_entities()

    # 2. Using ModelBasedEntityExtractor
    temp_file_uploader = TempFileUploader(TEMP_BUCKET)
    gcs_input_uri = temp_file_uploader.upload_file(file_path)

    prompt_extract = get_extract_entities_prompt()
    model_extractor = ModelBasedEntityExtractor(MODEL_NAME, prompt_extract, gcs_input_uri)
    gemini_entities = model_extractor.extract_entities()

    temp_file_uploader.delete_file()

    compare_prompt = get_compare_entities_prompt()
    compare_prompt = compare_prompt.format(
        docai_output=str(docai_entities), gemini_output=str(gemini_entities)
    )

    model = GenerativeModel(MODEL_NAME)
    docai_gemini_response_analysis = model.generate_content(compare_prompt)
    summary = docai_gemini_response_analysis.text
    print(summary)
    insert_document_firestore(src_fname, summary)


def insert_document_firestore(file_name: str, summary: str):
    data = {"name": file_name.split("/")[-1], "summary": summary}
    db.collection("files").document(file_name.split("/")[-1]).set(data)


def download_storage_tmp(src_bucket, src_fname):
    input_bucket = storage_client.bucket(src_bucket)
    input_blob = input_bucket.blob(src_fname)
    input_file_name = os.path.basename(src_fname)
    try:
        input_blob.download_to_filename(input_file_name)
    except NotFound as e:
        raise FileNotFoundError(f"File not found in bucket: {e}") from e
    return input_file_name
