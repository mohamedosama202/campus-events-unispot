"""
Local smoke test for the UniSpot app — runs against MOCKED AWS services
(via moto), so no real AWS account or costs are needed.
Run: python3 test_local.py
"""
import os
os.environ["AWS_REGION"] = "eu-central-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "eu-central-1"
os.environ["DYNAMODB_TABLE_NAME"] = "UniSpotEvents"
os.environ["S3_BUCKET_NAME"] = "unispot-event-images-test"

from moto import mock_aws

with mock_aws():
    import boto3
    # Create the mock bucket before the app module initializes its client
    s3 = boto3.client("s3", region_name="eu-central-1")
    s3.create_bucket(
        Bucket="unispot-event-images-test",
        CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
    )
    s3.put_object(Bucket="unispot-event-images-test", Key="events/squash.jpg", Body=b"fake-image-bytes")

    import seed_data
    seed_data.ensure_table_exists()
    seed_data.seed()

    import app as unispot_app

    client = unispot_app.app.test_client()

    print("=== TEST 1: Homepage loads and lists events ===")
    resp = client.get("/")
    assert resp.status_code == 200, f"Homepage failed: {resp.status_code}"
    body = resp.get_data(as_text=True)
    assert "UniSpot" in body
    assert "GIU Squash Open Tournament" in body, "Seeded event not found on homepage"
    print("PASS — homepage returns 200 and shows seeded events")

    print("\nALL TESTS PASSED")
