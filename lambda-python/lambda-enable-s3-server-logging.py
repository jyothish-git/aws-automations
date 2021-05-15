import json
import boto3
from botocore.config import Config
my_config = Config(region_name = 'us-east-1')
#This function enable server logging in all S3 bucket based on tag. If an S3 bucket tagged with
#"logging-enabled: true" then server logging will be enabled.
def lambda_handler(event, context):
    req = boto3.client('resourcegroupstaggingapi', config=my_config)
    out = req.get_resources(TagFilters=[{'Key': 'logging-enabled','Values':['true']}],ResourceTypeFilters=['s3'])
    print(out)
    if out['ResourceTagMappingList']:
        for i in out['ResourceTagMappingList']:
            bucket_name = i['ResourceARN'].split(':::')[-1]
            print(bucket_name)
            client = boto3.client('s3')
            client.put_object(Bucket='target-logging-bucket-names', Key=(bucket_name+'/'))
            s3 = boto3.resource('s3')
            bucket_logging = s3.BucketLogging(bucket_name)
            response = bucket_logging.put(BucketLoggingStatus={'LoggingEnabled': {'TargetBucket': 'target-logging-bucket-names', 'TargetPrefix': bucket_name + '/'}})
    else:
        print("No bucket found with the specified Tag")
