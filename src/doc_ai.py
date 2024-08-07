from typing import Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError
from google.cloud import documentai
from google.cloud import storage

import re
import uuid

from extractor import BatchDocumentExtractor
from extractor import OnlineDocumentExtractor
# Batch processing

project_id = "project-id"
location = "us"  # Or other supported locations like 'eu'
processor_id = "processor-id"
processor_version_id = "processor-version-id"  # Optional for batch processing
# File to process
file_path = "test_file.pdf"
mime_type = "application/pdf"



gcs_output_uri = "gs://bucket-output"  # GCS URI for output
gcs_temp_uri = "gs://bucket-temp"  # GCS URI for output


# batch_extractor = BatchDocumentExtractor(
#     project_id=project_id,
#     location=location,
#     processor_id=processor_id,
#     gcs_output_uri=gcs_output_uri,
#     gcs_temp_uri=gcs_temp_uri,
#     processor_version_id=processor_version_id,  # Optional
#     timeout=600,  # Optional timeout in seconds
# )
# batch_document = batch_extractor.process_document(file_path, mime_type)
# print("Batch Processed Document:", batch_document)


# Online processing
online_extractor = OnlineDocumentExtractor(
    project_id=project_id,
    location=location,
    processor_id=processor_id,
    # processor_version_id=processor_version_id
)
online_document = online_extractor.process_document(file_path, mime_type)


for entity in online_document.entities:
    print("Entity:", entity)
