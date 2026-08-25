"""
Local smoke test for the UniSpot app — runs against MOCKED AWS services
(via moto), so no real AWS account or costs are needed. Verifies:
  - table creation + seeding works
  - homepage renders and lists events
  - event detail page renders
  - S3 presigned URL generation works
  - registration POST updates DynamoDB
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

    print("\n=== TEST 2: Health check endpoint ===")
    resp = client.get("/healthz")
    assert resp.status_code == 200
    print("PASS —", resp.get_json())

    print("\n=== TEST 3: Event detail page ===")
    resp = client.get("/event/evt-001")
    assert resp.status_code == 200
    assert "GIU Squash Open Tournament" in resp.get_data(as_text=True)
    print("PASS — event detail page renders")

    print("\n=== TEST 4: S3 presigned URL is generated for the image ===")
    resp = client.get("/")
    body = resp.get_data(as_text=True)
    assert "amazonaws.com" in body or "X-Amz-Signature" in body, "No presigned S3 URL found in homepage HTML"
    print("PASS — presigned S3 URL present in rendered HTML")

    print("\n=== TEST 5: Registration increments count (bonus feature) ===")
    resp = client.post("/register/evt-001", follow_redirects=True)
    assert resp.status_code == 200
    detail = client.get("/event/evt-001").get_data(as_text=True)
    assert "1 registered" in detail, "Registration count did not increment"
    print("PASS — registration count incremented to 1")

    print("\n=== TEST 6: Missing event shows graceful error ===")
    resp = client.get("/event/does-not-exist")
    assert resp.status_code == 200
    assert "Event not found" in resp.get_data(as_text=True)
    print("PASS — graceful fallback for missing event")

    print("\nALL TESTS PASSED")
