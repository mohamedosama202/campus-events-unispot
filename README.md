# UniSpot — Scalable Campus Events Platform

![AWS](https://img.shields.io/badge/AWS-eu--north--1-FF9900?logo=amazonaws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?logo=flask&logoColor=white)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen)

A cloud-native web application that helps university students discover campus events,
club activities, workshops, sports tournaments, and social gatherings — deployed on a
secure, highly available, auto-scaling AWS architecture.

**Course:** ICS608 – Software Cloud Computing (Instructor: John Fayz)

**Live demo:** http://UniSpot-ALB-909099899.eu-north-1.elb.amazonaws.com

**GitHub Repository:** https://github.com/mohamedosama202/campus-events-unispot

---

## Table of Contents

- [Architecture](#architecture)
- [What's in this repo](#whats-in-this-repo)
- [Deployed AWS resources](#deployed-aws-resources)
- [Local Development](#local-development)
- [How it was deployed](#how-it-was-deployed)
- [Verified behaviors](#verified-behaviors)
- [Bonus features implemented](#bonus-features-implemented)
- [Notable challenge and fix](#notable-challenge-and-fix)
- [Cost estimate](#cost-estimate)
- [Team contributions](#team-contributions--team-6)
- [Cleanup](#cleanup)

---

## Architecture

![UniSpot Architecture Diagram](docs/architecture-diagram.png)

Users reach the application exclusively through the Application Load Balancer's DNS
name — never an EC2 public IP. The Load Balancer distributes traffic across EC2
instances managed by an Auto Scaling Group (min 1 / desired 2 / max 4, target-tracking
on CPU utilization). Application servers read event data from DynamoDB and event images
from S3, assuming a least-privilege IAM role rather than embedding credentials.
CloudWatch observes the whole stack and raises an alarm on sustained high CPU.

## What's in this repo

```
unispot/
├── app/                                Flask application (deployed to EC2)
│   ├── app.py                          Routes, DynamoDB integration, S3 presigned URLs, instance identity
│   ├── seed_data.py                    Creates the table (if needed) and loads 6 sample events
│   ├── test_local.py                   Local smoke test against mocked AWS services (no AWS costs)
│   ├── requirements.txt
│   ├── templates/                      index.html, event_detail.html, base.html
│   └── static/style.css
├── infrastructure/
│   ├── unispot-infrastructure.yaml     CloudFormation template — provisions the full stack
│   └── user-data.sh                    EC2 boot script (installs + runs the app)
├── iam/
│   ├── ec2-trust-policy.json           Trust policy for the EC2 role
│   └── ec2-role-policy.json            Least-privilege permissions (matches the CFN template)
└── docs/
    ├── architecture-diagram.svg / .png
    └── UniSpot_Project_Report.docx     Full project report with verification screenshots
```

## Deployed AWS resources

| Resource | Value |
|---|---|
| Region | eu-north-1 (Europe — Stockholm) |
| Load Balancer URL | http://UniSpot-ALB-909099899.eu-north-1.elb.amazonaws.com |
| DynamoDB table | UniSpotEvents (on-demand capacity, 6 seeded events, Point-in-Time Recovery enabled) |
| S3 event images bucket | unispot-event-images-490497823432 (private, versioned, lifecycle rule to IA) |
| Auto Scaling Group | UniSpot-ASG (min 1 / desired 2 / max 4, target-tracking CPU scaling) |
| IAM role | UniSpot-EC2-Role (SSM + scoped S3 read-only + scoped DynamoDB read/write — no admin access) |
| CloudWatch | UniSpot-Dashboard, UniSpot-HighCPU alarm (SNS-connected) |

## Local Development

The app can be run and tested entirely on your own machine — no AWS account or costs
required — using mocked AWS services.

```bash
# 1. Clone the repo
git clone https://github.com/mohamedosama202/campus-events-unispot.git
cd campus-events-unispot/app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the local smoke test (uses moto to mock DynamoDB/S3)
python3 test_local.py
```

`test_local.py` verifies table creation and seeding, homepage rendering, event detail
rendering, S3 presigned URL generation, and the registration flow — all without touching
real AWS resources.

## How it was deployed

```bash
# 1. Package and upload the app code to the deployment bucket
cd app
zip -r ../unispot-app.zip . -x "__pycache__/*" -x "*.pyc"
cd ..
aws s3 mb s3://unispot-deploy-490497823432 --region eu-north-1
aws s3 cp unispot-app.zip s3://unispot-deploy-490497823432/unispot-app.zip
aws s3 cp infrastructure/user-data.sh s3://unispot-deploy-490497823432/user-data.sh

# 2. Deploy the CloudFormation stack
aws cloudformation deploy \
  --template-file infrastructure/unispot-infrastructure.yaml \
  --stack-name unispot \
  --region eu-north-1 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      VpcId=vpc-0c1841ead2b310db8 \
      SubnetIds=subnet-03d883da246f26dd5,subnet-01df1971b892a4243,subnet-0bfd6d255d1166829 \
      DeploymentBucketName=unispot-deploy-490497823432

# 3. Seed DynamoDB with sample events
cd app
AWS_REGION=eu-north-1 DYNAMODB_TABLE_NAME=UniSpotEvents python3 seed_data.py
cd ..

# 4. Upload event images
aws s3 cp squash.jpg s3://unispot-event-images-490497823432/events/squash.jpg
# ...repeat for design-sprint.jpg, career-talk.jpg, market-day.jpg, study-jam.jpg, robotics-fair.jpg

# 5. Get the Load Balancer URL
aws cloudformation describe-stacks --stack-name unispot --region eu-north-1 \
  --query "Stacks[0].Outputs" --output table
```

## Verified behaviors

All of the following were tested live against the deployed stack (full evidence —
screenshots and command output — is in `docs/UniSpot_Project_Report.docx`, Appendix A):

- **Load distribution** — the homepage footer shows a different `instance_id` across
  repeated requests, confirmed via `curl` loop against the ALB DNS name.
- **Failover** — stopping one EC2 instance (`aws ec2 stop-instances`) leaves the
  application fully available, served by the remaining healthy instance.
- **Self-healing** — the Auto Scaling Group detects the unhealthy instance and
  automatically launches a replacement, with zero manual intervention.
- **Health checks** — the ALB target group reports per-instance healthy/unhealthy state.
- **Monitoring** — CloudWatch dashboard tracks EC2 CPU, ALB request count,
  healthy/unhealthy host count, and ASG in-service instance count; the `UniSpot-HighCPU`
  alarm fires at >70% CPU for two consecutive periods.
- **Security** — IAM role grants only the specific S3/DynamoDB permissions the app needs
  (no `AdministratorAccess`); the EC2 security group only accepts traffic from the ALB's
  security group, not the public internet; SSH is disabled in favor of AWS Systems
  Manager.
- **Data durability** — S3 bucket versioning is enabled, with a lifecycle rule
  transitioning older image versions to Standard-IA storage.

## Bonus features implemented

Beyond the required components, the following optional bonus features were implemented
and verified:

- **Event search and category filters** — the homepage includes clickable category chips
  (All, Academic, Career, Clubs, Social, Sports, Workshop) that filter the visible events
  client-side without a page reload.
- **DynamoDB Point-in-Time Recovery** — continuous backups with PITR are enabled on the
  `UniSpotEvents` table (35-day recovery window), verified via
  `aws dynamodb describe-continuous-backups`.
- **SNS notification connected to the CloudWatch alarm** — an SNS topic
  (`UniSpot-Alerts`) is subscribed to the team's email and attached as an alarm action on
  `UniSpot-HighCPU`, so the team is notified automatically if CPU exceeds the 70%
  threshold.
- **Responsive interface for mobile devices** — dedicated CSS media queries (max-width
  640px and 380px) reflow the layout for phone-sized screens: the event grid collapses to
  a single column, buttons become full-width, and header/hero text sizes adjust. Verified
  on both desktop and mobile viewport widths.

## Notable challenge and fix

Event images initially failed to load with `AccessDenied` errors despite correct IAM
permissions and application logic. The root cause: the boto3 S3 client was generating
presigned URLs against the global `s3.amazonaws.com` endpoint while the signature was
scoped to `eu-north-1` — a mismatch AWS rejects for any region other than `us-east-1`.
Fixed by explicitly setting `endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"` on
the S3 client, then rolling out the fix via an Auto Scaling Group instance refresh with
zero downtime. Full writeup in the project report.

## Cost estimate

~$35.26/month for the deployed stack (2x t3.micro EC2, 1 ALB, DynamoDB on-demand, S3,
CloudWatch), based on the official AWS Pricing Calculator:
https://calculator.aws/#/estimate?id=e1ae0f302172dd1d68c5e47f4b350b55851e1dde

## Team contributions — Team 6

| Team Member | Contribution |
|---|---|
| Mohamed Osama | Flask backend (`app.py`: routes, DynamoDB and S3 integration, health check); project report |
| Yassin Waleed & Saged Mohamed | Database seeding (`seed_data.py`) and local application testing (`test_local.py`) |
| Fares Sadek Galal & Hussein Sherif | AWS infrastructure setup and configuration (EC2, ALB, Auto Scaling Group, CloudFormation template, server startup script) |
| Jumana Mohab | IAM roles and policies, ensuring least-privilege access for the EC2 instance role |
| Mohamed Khalid Naguib | Frontend templates (homepage, event detail pages) and static styling |

## Cleanup

After grading is complete, tear down the stack to stop all charges:

```bash
aws s3 rm s3://unispot-event-images-490497823432 --recursive
aws s3 rm s3://unispot-deploy-490497823432 --recursive
aws cloudformation delete-stack --stack-name unispot --region eu-north-1
```
