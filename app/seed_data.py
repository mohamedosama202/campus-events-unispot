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


SAMPLE_EVENTS = [
    {
        "event_id": "evt-001",
        "name": "GIU Squash Open Tournament",
        "category": "Sports",
        "date": "2026-09-05",
        "location": "GIU Sports Complex",
        "available_spaces": 32,
        "registration_count": 0,
        "image_key": "events/squash.jpg",
        "description": "Annual campus-wide squash tournament, open to all skill levels. Sign-ups close a week before the event.",
    },
    {
        "event_id": "evt-002",
        "name": "HCI Design Sprint Workshop",
        "category": "Workshop",
        "date": "2026-09-10",
        "location": "Informatics Building, Room 214",
        "available_spaces": 25,
        "registration_count": 0,
        "image_key": "events/design-sprint.jpg",
        "description": "A hands-on workshop covering rapid prototyping, Nielsen's heuristics, and usability testing basics.",
    },
    {
        "event_id": "evt-003",
        "name": "Cloud & Distributed Systems Career Talk",
        "category": "Career",
        "date": "2026-09-14",
        "location": "Main Auditorium",
        "available_spaces": 150,
        "registration_count": 0,
        "image_key": "events/career-talk.jpg",
        "description": "Industry engineers discuss careers in cloud infrastructure, distributed systems, and site reliability engineering.",
    },
    {
        "event_id": "evt-004",
        "name": "Fresh Fruits Market Day",
        "category": "Social",
        "date": "2026-09-18",
        "location": "Central Campus Plaza",
        "available_spaces": 500,
        "registration_count": 0,
        "image_key": "events/market-day.jpg",
        "description": "Student clubs and local vendors set up stalls for a relaxed afternoon market on the plaza.",
    },
    {
        "event_id": "evt-005",
        "name": "Data Structures Study Jam",
        "category": "Academic",
        "date": "2026-09-21",
        "location": "Library, Group Study Room B",
        "available_spaces": 20,
        "registration_count": 0,
        "image_key": "events/study-jam.jpg",
        "description": "Peer-led review session covering BSTs, stacks, queues, and deques ahead of the midterm.",
    },
    {
        "event_id": "evt-006",
        "name": "Club Fair: Robotics & AI Society",
        "category": "Clubs",
        "date": "2026-09-25",
        "location": "Engineering Courtyard",
        "available_spaces": 200,
        "registration_count": 0,
        "image_key": "events/robotics-fair.jpg",
        "description": "Meet the Robotics & AI Society, see live demos, and sign up for upcoming project teams.",
    },
]


def seed():
    table = dynamodb.Table(TABLE_NAME)
    with table.batch_writer() as batch:
        for event in SAMPLE_EVENTS:
            batch.put_item(Item=event)
    print(f"Seeded {len(SAMPLE_EVENTS)} events into '{TABLE_NAME}'.")


if __name__ == "__main__":
    ensure_table_exists()
    seed()
