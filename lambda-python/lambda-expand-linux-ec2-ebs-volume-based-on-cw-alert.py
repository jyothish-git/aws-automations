import boto3
import json
import time
import re

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    ssm_client = boto3.client('ssm')
    partition_number = ''
    data = event['Records'][0]['Sns']['Message']
    data = json.loads(data)
    print(data['Trigger']['Dimensions'])
    required_data = data['Trigger']['Dimensions']
    for item in required_data:
        print(item)
        if item['name'] == 'path':
            mount_point = item['value']
        elif item['name'] == 'InstanceId':
            instance_id = item['value']
        elif item['name'] == 'device':
            device_id = item['value']
        elif item['name'] == 'fstype':
            filesystem_type = item['value']

    print("Instance ID: " + instance_id)
    print("Device ID: " + device_id)
    print("Device Mount Point: " + mount_point)
    print("File System Type: " + filesystem_type)

    try:
        ec2_device_mapping = ec2_client.describe_instance_attribute(Attribute='blockDeviceMapping', InstanceId=instance_id)
    except Exception as error:
        print(error)

    print(ec2_device_mapping)

    match = re.search(r'\d+$', device_id[-1])
    if match:
        partition_number = device_id[-1]
        end_char_device_id = device_id[:-1][-1]
        print(end_char_device_id)
    else:
        end_char_device_id = device_id[-1]
        print(end_char_device_id)
    for item in ec2_device_mapping['BlockDeviceMappings']:
        end_char_ebs_id = item['DeviceName'][-1]
        print(end_char_ebs_id)
        if end_char_device_id == end_char_ebs_id:
            ebs_volume_id = item['Ebs']['VolumeId']
            print("AWS EBS Volume ID: " + ebs_volume_id)

    current_volume_size = ec2_resource.Volume(ebs_volume_id).size
    required_volume_size = int(current_volume_size * 0.2 + current_volume_size)
    print("Current EBS volume size: " + str(current_volume_size) + " Gb")
    print("Required EBS volume size: " + str(required_volume_size) + " Gb")

    try:
        print("Modifying the EBS volume " + ebs_volume_id + " size")
        ec2_client.modify_volume(VolumeId=ebs_volume_id, Size=required_volume_size)
        print('EBS volume modification complete')

    except Exception as error:
        print(error)

    time.sleep(240)

    print("Starting file system re-sizing")
    if partition_number:
        command1 = 'sudo su'
        command2 = 'growpart /dev/' + device_id[:-1] + " "+ partition_number
        if filesystem_type.startswith('xfs'):
            command3 = 'xfs_growfs -d '+ mount_point
        elif filesystem_type.startswith('ext'):
            command3 = 'resize2fs /dev/' + device_id
        else:
            print("error: filesystem not supported")
            exit()
        try:
            response = ssm_client.send_command(InstanceIds=[instance_id], DocumentName="AWS-RunShellScript", Parameters={'commands': [command1, command2, command3]} )
            print(response)
            print("Activity completed.")
        except Exception as error:
            print(error)
    else:
        command1 = 'sudo su'
        if filesystem_type.startswith('xfs'):
            command2 = 'xfs_growfs -d '+ mount_point
        elif filesystem_type.startswith('ext'):
            command2 = 'resize2fs /dev/' + device_id
        else:
            print("error: filesystem not supported")
            exit()
        try:
            response = ssm_client.send_command(InstanceIds=[instance_id], DocumentName="AWS-RunShellScript", Parameters={'commands': [command1, command2]} )
            print(response)
            print("Activity completed.")
        except Exception as error:
            print(error)
