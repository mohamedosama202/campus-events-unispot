"""
UniSpot - A Scalable Campus Events Platform
Flask application that reads events from DynamoDB, serves images from S3,
and reports its own EC2 instance identity (to demonstrate ALB load
distribution across multiple instances).
"""

import os
from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "unispot-dev-secret")

# ---------------------------------------------------------------------------
# Configuration (populated via environment variables set by the EC2
# user-data script / Launch Template — never hardcode these).
# ---------------------------------------------------------------------------
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "UniSpotEvents")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "unispot-event-images")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def homepage():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
