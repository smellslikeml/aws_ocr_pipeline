#!/usr/bin/env python
import os
import shlex
import boto3
import shutil
import subprocess
from time import sleep
from glob import glob
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['DEFAULT']

BUCKET_IN = config['BUCKET_IN']
BUCKET_OUT = config['BUCKET_OUT']
QUEUE = config['QUEUE']
REGION_NAME = config['REGION_NAME']

# Gather network information on instance
meta_id = subprocess.Popen(['ec2metadata', '--instance-id'], stdout=subprocess.PIPE)
ids = meta_id.stdout.read().strip('\n')
avl_zn = subprocess.Popen(['ec2metadata', '--availability-zone'], stdout=subprocess.PIPE)
zn = avl_zn.stdout.read().strip('\n')

# instantiate client
ec2 = boto3.resource('ec2', region_name=REGION_NAME)
client = boto3.client('ec2', REGION_NAME)
sqs = boto3.resource('sqs', region_name=REGION_NAME)

queue = sqs.get_queue_by_name(QueueName=QUEUE)

# Mount additional storage volume
vol = client.create_volume(AvailabilityZone=zn, Size=80, VolumeType='io1', Iops=1000, Encrypted=True)
sleep(10)
att = client.attach_volume(VolumeId=vol['VolumeId'], InstanceId=ids, Device='/dev/sdb')
sleep(20)

# Mount the new volume
subprocess.call(["sudo", "mkfs", "-t", "ext4", "/dev/xvdb"])
subprocess.call(["sudo", "mkdir", "/ocr_docs"])
subprocess.call(["sudo", "mount", "/dev/xvdb", "/ocr_docs"])

# Build data directories
subprocess.call(["sudo", "chown", "-R", "ec2-user:ec2-user", "/ocr_docs"])
subprocess.call(["mkdir", "/ocr_docs/msg"])
subprocess.call(["mkdir", "/ocr_docs/s3"])


N = int(queue.attributes['ApproximateNumberOfMessages'])
while N > 0:
    msgs = queue.receive_messages(MaxNumberOfMessages=10, MessageAttributeNames=['All'])
    for msg in msgs:
        cmd = "aws s3 cp --region {}".format(REGION_NAME) + " s3://{}/".format(BUCKET_IN) +  msg.body + "/ocr_docs/msg/" + msg.body
        subprocess.call(cmd, shell=True)

    os.chdir('/ocr_docs/msg/')
    for msg in glob('*'):
	cmd = "grep -v '^#' " + msg + " | parallel -j0 aws s3 cp s3://{}".format(BUCKET_IN) + "/{} /ocr_docs/s3/ --region {} --sse".format(REGION_NAME)
	ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = ps.communicate()[0]
        os.remove(msg)
    os.chdir('/ocr_docs/s3/')
    proc1= subprocess.Popen(shlex.split("find ./ -type f -name '*.pdf'"),stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split(' parallel -j0 convert -density 300 -depth 8 -alpha off {} -compress lzw {.}.tif'),stdin=proc1.stdout, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc1.stdout.close()
    out,err=proc2.communicate()
    proc1= subprocess.Popen(shlex.split("find ./ -type f -name '*.tif'"),stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split(' parallel -j0 convert {} +adjoin -gravity north -crop 95%x100%+0-100 +repage -adjoin {.}.tif'),stdin=proc1.stdout, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc1.stdout.close()
    out,err=proc2.communicate()
    proc1= subprocess.Popen(shlex.split("find ./ -type f -name  '*.tif'"),stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(shlex.split('parallel -j0 tesseract -l eng {} {.}'),stdin=proc1.stdout, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc1.stdout.close()
    out,err=proc2.communicate()

    cmd = "aws s3 cp --recursive --region {} /ocr_docs/s3/ s3://{}".format(REGION_NAME, BUCKET_OUT) + "/ --include '*' --exclude '*.doc' --exclude '*.tif' --sse"
    subprocess.call(cmd, shell=True)
    sleep(300)
    for msg in msgs:
        msg.delete()
    lst = os.listdir('/ocr_docs/s3/')
    for ff in lst:
        try:
            os.remove(ff)
        except:
            shutil.rmtree(ff)
    N = int(queue.attributes['ApproximateNumberOfMessages'])



# Terminate instance
ec2.instances.filter(InstanceIds=[ids]).terminate()
