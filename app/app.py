"""
UniSpot - A Scalable Campus Events Platform
Flask application that reads events from DynamoDB, serves images from S3,
and reports its own EC2 instance identity (to demonstrate ALB load
distribution across multiple instances).
"""

import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from flask import Flask, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "unispot-dev-secret")

# ---------------------------------------------------------------------------
# Configuration (populated via environment variables set by the EC2
# user-data script / Launch Template — never hardcode these).
# ---------------------------------------------------------------------------
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "UniSpotEvents")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "unispot-event-images")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION, endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_presigned_image_url(image_key, expires_in=3600):
    """
    Generates a time-limited presigned URL for an S3 object instead of
    making the bucket/object public. This satisfies 'block public access'
    while still letting the browser load event images directly from S3.
    """
    if not image_key:
        return None
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": image_key},
            ExpiresIn=expires_in,
        )
    except ClientError as exc:
        app.logger.error("Failed to presign %s: %s", image_key, exc)
        return None


def fetch_events():
    """Scans the DynamoDB table and returns events sorted by date."""
    try:
        response = table.scan()
        items = response.get("Items", [])
        for item in items:
            item["image_url"] = get_presigned_image_url(item.get("image_key"))
        items.sort(key=lambda e: e.get("date", ""))
        return items
    except ClientError as exc:
        app.logger.error("DynamoDB scan failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def homepage():
    events = fetch_events()
    categories = sorted({e.get("category", "General") for e in events})
    return render_template(
        "index.html",
        events=events,
        categories=categories,
        now=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )


@app.route("/event/<event_id>")
def event_detail(event_id):
    try:
        response = table.get_item(Key={"event_id": event_id})
        event = response.get("Item")
    except ClientError as exc:
        app.logger.error("DynamoDB get_item failed: %s", exc)
        event = None

    if event:
        event["image_url"] = get_presigned_image_url(event.get("image_key"))

    return render_template("event_detail.html", event=event)


@app.route("/register/<event_id>", methods=["POST"])
def register_interest(event_id):
    """
    BONUS: atomically increments the registration count for an event.
    Requires the EC2 IAM role to include dynamodb:UpdateItem.
    """
    try:
        table.update_item(
            Key={"event_id": event_id},
            UpdateExpression="SET registration_count = if_not_exists(registration_count, :zero) + :inc",
            ExpressionAttributeValues={":inc": 1, ":zero": 0},
        )
        flash("You're registered! See you there.", "success")
    except ClientError as exc:
        app.logger.error("DynamoDB update_item failed: %s", exc)
        flash("Could not register right now — please try again.", "error")

    return redirect(url_for("event_detail", event_id=event_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
