import os
import boto3
import re

s3 = boto3.resource('s3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin')
minio = s3.Bucket('mlflow')

#for item in minio.objects.filter(Prefix = '0'):
#    print(item.key)
files = filter(lambda x:x.endswith("model.pkl"), minio.objects)
for item in files:
    print(item.key)
minio.download_file('0/52703bb76aca44488ed8f12de7dea74e/artifacts/rf-regressor/model.pkl', 'model.pkl')

        
#minio = boto3.resource('s3',
#                endpoint_url='http://localhost:9000',
#                aws_access_key_id='minioadmin',
#                aws_secret_access_key='minioadmin')
#minio.Bucket('mlflow').download_file('model.pkl', '0/bf2ac09f0f02457ca616cbc140888957/artifacts/rf-regressor/')
