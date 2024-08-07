from typing import Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError
from google.cloud import documentai
from google.cloud import storage

import re
import uuid


class DocumentExtractor:
    """
    Base class for Document Extractors using Google Document AI.
    """

    def __init__(self, project_id: str, location: str, processor_id: str,
                 processor_version_id: Optional[str] = None):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.processor_version_id = processor_version_id
        self.client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(
                api_endpoint=f"{location}-documentai.googleapis.com"
            )
        )
        self.processor_name= self._get_proccessor_name()
        
    def _get_proccessor_name(self):
        if self.processor_version_id:
            return self.client.processor_version_path(
                self.project_id, self.location, self.processor_id, self.processor_version_id
            )  
        else:
            return self.client.processor_path(
                self.project_id, self.location, self.processor_id
            )

    def process_document(self, file_path: str, mime_type: str) -> documentai.Document:
        """
        Abstract method to be implemented by subclasses.
        Processes a document using the specified Document AI processor.
        """
        raise NotImplementedError

class OnlineDocumentExtractor(DocumentExtractor):
    """
    Processes documents using the online Document AI API.
    """
    def process_document(self, file_path: str, mime_type: str) -> documentai.Document:
        
        with open(file_path, "rb") as image:
            image_content = image.read()

        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=documentai.RawDocument(content=image_content, mime_type=mime_type)
        )

        result = self.client.process_document(request=request)
        return result.document


class BatchDocumentExtractor(DocumentExtractor):
    """
    Processes documents using the batch Document AI API.
    """
    def __init__(self, project_id: str, location: str, processor_id: str, gcs_output_uri: str,
                 gcs_temp_uri: str,processor_version_id: str, timeout: int = 400):
        super().__init__(project_id, location, processor_id, processor_version_id)
        self.gcs_output_uri = gcs_output_uri
        self.gcs_temp_uri = gcs_temp_uri
        self.timeout = timeout
        self.storage_client= storage.Client()
        
        path_parts = gcs_temp_uri.replace("gs://", "").split('/')
        self.temp_bucket_name = path_parts[0]
        self.temp_file_path_gcs = '/'.join(path_parts[1:])
        
    def _get_destination_blob_name(self, file_path: str) -> str:
        file_id = str(uuid.uuid4())
        file_extension = file_path.split('.')[-1]
        destination_blob_name = f"{self.temp_file_path_gcs}{file_id}.{file_extension}"
        return destination_blob_name

    def process_document(self, file_path: str, mime_type: str) -> documentai.Document:              
        destination_blob_name=self._get_destination_blob_name(file_path)        

        # Upload file to GCS
        bucket = self.storage_client.bucket(self.temp_bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        
        gcs_input_uri = f"gs://{self.temp_bucket_name}/{destination_blob_name}"
        document = self._process_document_batch(gcs_input_uri, mime_type)
        blob.delete()
        return document

    def _process_document_batch(self, gcs_input_uri: str, mime_type: str) -> documentai.Document:        

        gcs_document = documentai.GcsDocument(
            gcs_uri=gcs_input_uri, mime_type=mime_type
        )
        gcs_documents = documentai.GcsDocuments(documents=[gcs_document])
        input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_documents)

        gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
            gcs_uri=self.gcs_output_uri
        )
        output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

        request = documentai.BatchProcessRequest(
            name=self.processor_name,
            input_documents=input_config,
            document_output_config=output_config,
        )

        operation = self.client.batch_process_documents(request)
        try:
            print(f"Waiting for operation ({operation.operation.name}) to complete...")
            operation.result(timeout=self.timeout)
        except (RetryError, InternalServerError) as e:
            print(e.message)

        metadata = documentai.BatchProcessMetadata(operation.metadata)
        if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
            raise ValueError(f"Batch Process Failed: {metadata.state_message}")

        # Retrieve the processed document from GCS
        for process in list(metadata.individual_process_statuses):
            matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
            if not matches:
                print(
                    "Could not parse output GCS destination:",
                    process.output_gcs_destination,
                )
                continue

            output_bucket, output_prefix = matches.groups()
            output_blobs = self.storage_client.list_blobs(output_bucket, prefix=output_prefix)
            for blob in output_blobs:
                if blob.content_type == "application/json":
                    print(f"Fetching {blob.name}")
                    return documentai.Document.from_json(
                        blob.download_as_bytes(), ignore_unknown_fields=True
                    )

        raise FileNotFoundError("Processed document not found in GCS.")