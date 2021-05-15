from datetime import datetime, timezone
import boto3

def lambda_handler(event, context):
    #change the bucket name & region code as per your requirement
    thebucket = "bucket-name-here"
    region_name = "us-west-2"
    s3 = boto3.resource("s3", region_name=region_name)
    s3client = boto3.client("s3")
    # paginate 100000 at a time
    page_size = 100000
    folder_in_thebucket = "folder1/files"
    paginator = s3client.get_paginator("list_object_versions")
    pageresponse = paginator.paginate(Bucket=thebucket, Prefix=folder_in_thebucket, PaginationConfig={"MaxItems": page_size})
    #dont put date like this 2021, 03, 17...leading zero is not supported
    #deleted_at = datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

    for pageobject in pageresponse:
        print("1executing here")
        if 'DeleteMarkers' in pageobject.keys():
            print("2executing here")
            for each_delmarker in pageobject['DeleteMarkers']:
                print("3executing here")
                print(each_delmarker)
                #if each_delmarker["IsLatest"] is True and each_delmarker["LastModified"] > deleted_at:
                if each_delmarker["IsLatest"] is True:
                    print("4executing here")
                    fileobjver = s3.ObjectVersion(thebucket,each_delmarker['Key'],each_delmarker['VersionId'])
                    print('Restoring ' + each_delmarker['Key'])
                    fileobjver.delete()
