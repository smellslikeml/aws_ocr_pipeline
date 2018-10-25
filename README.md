# Distributed OCR with AWS

Uses boto3 to start a group of EC2 instances, based on an AMI configured with Tesseract and GNU-Parallel to perform OCR on batches of documents queued in SQS.

## Usage

First, configure your EC2 instance by running the following: 
```
bash install.sh
```
After successfully building tesseract and dependencies, record the instance AMI id into the config.ini file. Add your bucket names and declare the parameters in the config.ini

* BUCKET_IN is a bucket with raw image and pdf files.
* BUCKET_OUT is a bucket where OCR'd text will be kept.
* QUEUE is an SQS queue using messages to coordinate machines.

Now, run:
```
python aws_ocr_pipeline.py
```
