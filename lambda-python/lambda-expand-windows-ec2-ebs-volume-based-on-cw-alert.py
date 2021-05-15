import boto3
import json
import time
import re

win_details = [
    {"i-xxxxxxxxxxxxxxxx1": {"C" : "/dev/sda", "D": "/dev/sdb"}},
    {"i-xxxxxxxxxxxxxxxx2": {"C" : "/dev/sda1", "D": "/dev/sdg", "E": "/dev/sdf"}},
    {"i-xxxxxxxxxxxxxxxx3": {"C" : "/dev/sda", "F": "/dev/sdi"}}
            ]

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    ssm_client = boto3.client('ssm')
    data = event['Records'][0]['Sns']['Message']
    data = json.loads(data)
    print(data['Trigger']['Dimensions'])
    required_data = data['Trigger']['Dimensions']
    for item in required_data:
        if item['name'] == 'InstanceId':
            instance_id = item['value']
            print("Instance ID: " +instance_id)

        if item['name'] == 'instance':
            drive_name = item['value'].rstrip(":")
            print("Drive Name: " + drive_name)

    for item in win_details:
        if instance_id in item:
            device_id = item[instance_id][drive_name]
            print("Device ID: " + device_id)

    try:
        ec2_device_mapping = ec2_client.describe_instance_attribute(Attribute='blockDeviceMapping', InstanceId=instance_id)
    except Exception as error:
        print(error)

    print(ec2_device_mapping)
    for item in ec2_device_mapping['BlockDeviceMappings']:
        if item['DeviceName'] == device_id:
            ebs_volume_id = item['Ebs']['VolumeId']
            print("Ebs Volume ID: " + item['Ebs']['VolumeId'])
    current_volume_size = ec2_resource.Volume(ebs_volume_id).size
    required_volume_size = int(current_volume_size * 0.2 + current_volume_size)
    print("Current EBS volume size: " + str(current_volume_size) + " Gb")
    print("Required EBS volume size: " + str(required_volume_size) + " Gb")
    incremental_size = required_volume_size - 2
    print(incremental_size)

    try:
        print("Modifying the EBS volume " + ebs_volume_id + " size")
        ec2_client.modify_volume(VolumeId=ebs_volume_id, Size=required_volume_size)
        print('EBS volume modification complete')
    except Exception as error:
        print(error)

    time.sleep(240)

    print("Starting file system re-sizing")
    command1 = 'Resize-Partition -DriveLetter ' + drive_name + ' -Size ' + str(incremental_size) +'GB'
    try:
        response = ssm_client.send_command(InstanceIds=[instance_id], DocumentName="AWS-RunPowerShellScript", Parameters={'commands': [command1]} )
        print(response)
        print("Activity completed.")
    except Exception as error:
        print(error)
