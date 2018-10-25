#!/usr/bin/env python
import sys
import boto3
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['DEFAULT']

BUCKET_IN = config['BUCKET_IN']
QUEUE = config['QUEUE']
CHUNK_SIZE = int(config['CHUNK_SIZE'])
KEY_ID = config['KEY_ID']
AMI_ID = config['AMI_ID']
SG_GRP = config['SG_GRP']
IAM_NAME = config['IAM_NAME']
KEY_NAME = config['KEY_NAME']
BUCKET_CODE = config['BUCKET_CODE']
ins_typ = config['ins_typ']
num_instances = int(config['num_instances'])

userdata = """#!/bin/bash
aws s3 cp s3://{}/config.ini /home/ec2-user/ --region {}
aws s3 cp s3://{}/aws_ocr_runner.py /home/ec2-user/ --region {}
sudo chmod +x /home/ec2-user/aws_ocr_runner.py
/home/ec2-user/aws_ocr_runner.py
""".format(BUCKET_CODE, REGION_NAME, BUCKET_CODE, REGION_NAME)

# Provision resources
ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')
sqs = boto3.resource('sqs')

# Instantiate buckets & queues
s3_client = boto3.client('s3')
ec2_client = boto3.client('ec2')
sqs_client = boto3.client('sqs')

# Verify access to buckets
AVAIL_QUEUES = [url.split('/')[-1] for url in sqs_client.list_queues()['QueueUrls']]
if QUEUE in AVAIL_QUEUES:
    queue = sqs.get_queue_by_name(QueueName=QUEUE)
else:
    sys.exit()
AVAIL_BUCKETS = [bkt.name for bkt in s3.buckets.all()]
if (BUCKET_IN in AVAIL_BUCKETS):
    bucket = s3.Bucket(BUCKET_IN)
else:
    sys.exit()


# Define helper functions
def chunker(l, N):
    for idx in range(0, len(l), N):
        yield l[idx:idx + N]


# Chunk list of files
obj_lst = [f.key for f in bucket.objects.all()]
obj_chunks = list(chunker(obj_lst, CHUNK_SIZE))

for idx, chunk in enumerate(obj_chunks):
    msg = '\n'.join(chunk)
    s3_client.put_object(Bucket=BUCKET_IN,
                  Key='chunk_{}.bin'.format(idx), Body=msg,
                  ServerSideEncryption='aws:kms',
                  SSEKMSKeyId=KEY_ID)
    response = queue.send_message(MessageBody='chunk_{}.bin'.format(idx))

instance_lst = ec2.create_instances(ImageId=AMI_ID, 
                                    MinCount=num_instances, 
                                    MaxCount=num_instances, 
                                    InstanceType=ins_typ, 
                                    SecurityGroupIds=[SG_GRP], 
                                    UserData=userdata, 
                                    IamInstanceProfile={'Name': IAM_NAME}, 
                                    KeyName=KEY_NAME)
