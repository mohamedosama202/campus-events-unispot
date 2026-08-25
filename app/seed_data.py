"""
Creates the UniSpot DynamoDB table (if it doesn't exist) and seeds it with
sample events. Run this once after the table/S3 bucket are provisioned:

    AWS_REGION=eu-central-1 DYNAMODB_TABLE_NAME=UniSpotEvents python seed_data.py

Note: if you deployed via the CloudFormation template, the table is already
created for you — this script only needs to run the seeding part.
"""

import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "UniSpotEvents")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


def ensure_table_exists():
    try:
        dynamodb.meta.client.describe_table(TableName=TABLE_NAME)
        print(f"Table '{TABLE_NAME}' already exists.")
        return
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

    print(f"Creating table '{TABLE_NAME}'...")
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print("Table created.")


if __name__ == "__main__":
    ensure_table_exists()
