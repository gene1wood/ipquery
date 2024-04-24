#!/bin/env python

import boto3
import botocore.exceptions
import os.path, time, sys
import json
import yaml
from datetime import datetime

CONFIG_FILENAME = '/etc/ipquery.yaml'
config_last_modified = datetime.fromtimestamp(os.path.getmtime(CONFIG_FILENAME))

with open(CONFIG_FILENAME) as f:
    config = yaml.load(f)

if 'iam_role_type' in config and len(config['iam_role_type']) > 0:
    iam_role_type = config['iam_role_type']
else:
    sys.exit(0)

client = boto3.client('s3')

try:
    response = client.get_object(
        Bucket='infosec-internal-data',
        IfModifiedSince=config_last_modified,
        Key='iam-roles/roles.json'
    )
except botocore.exceptions.ClientError as e:
    if '304' not in e.message or 'Not Modified' not in e.message:
        raise
    # print("IAM Roles have not changed")
    sys.exit(0)

iam_role_map = json.loads(response['Body'].read())
arns = [x['Arn'].encode('ascii','replace')
        for x
        in iam_role_map
        if x['Type'] == iam_role_type]
config['ip2instance_roles'] = arns
with open(CONFIG_FILENAME, 'w') as f:
    yaml.dump(config, f, default_flow_style=False)

# TODO : Trigger apache httpd reload/restart