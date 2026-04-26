import boto3
from config import *

ec2 = boto3.resource('ec2')
def launch_instance():
    instance = ec2.create_instances(
        ImageId=AMI_ID,
        MinCount=1,
        MaxCount=1,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[SECURITY_GROUP],
        SubnetId=SUBNET_ID,
        UserData='''#!/bin/bash
/home/ubuntu/start.sh
'''
    )[0]

    instance.wait_until_running()
    instance.reload()
    ip = instance.private_ip_address

    print(f"Launched: {instance.id} | IP: {ip}")
    return instance.id, ip


def terminate_instance(instance_id):
    ec2.Instance(instance_id).terminate()
    print(f"Terminated: {instance_id}")
