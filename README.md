# Document AI and Gemini
Code example to use Document AI and Gemini for document extraction.

This repository assumes, that this [codelab](https://www.cloudskillsboost.google/focuses/67855?parent=catalog) has been completed, that a dataset with the test documents is available and there exists a Document AI extractor.

Once it has been completed, additionally create two buckets, for batch processing, namely, temp and output.

```bash
TEMP_BUCKET_URI = f"gs://documentai-temp-{PROJECT_ID}-unique"

gsutil mb -l {LOCATION} -p {PROJECT_ID} {BUCKET_URI}

OUT_BUCKET_URI = f"gs://documentai-temp-{TEMP_BUCKET_URI}-unique"

gsutil mb -l {LOCATION} -p {PROJECT_ID} {OUT_BUCKET_URI}
```

 
