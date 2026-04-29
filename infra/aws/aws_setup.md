# AWS Setup: Snowflake S3 Storage Integration

This document covers the AWS-side infrastructure that backs the Snowflake external stage used
to load parquet snapshots into `BASEBALL.RAW`.

For the Snowflake side, see `../snowflake/01_storage_integration.sql` and
`../snowflake/02_stage_and_file_formats.sql`.

Reference: [Snowflake docs — Configuring a Snowflake storage integration to access Amazon S3](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration)

---

## Key Resource Summary

| Resource              | Name / Value                                              |
| --------------------- | --------------------------------------------------------- |
| AWS Account ID        | `<AWS_ACCOUNT_ID>`                                        |
| S3 Bucket             | `<BUCKET_NAME>`                                           |
| IAM Role              | `<IAM_ROLE_NAME>` (e.g. `snowflake-baseball-integration`) |
| IAM Role ARN          | `arn:aws:iam::<AWS_ACCOUNT_ID>:role/<IAM_ROLE_NAME>`      |
| Snowflake Integration | `s3_baseball_analytics_integration`                       |
| Snowflake Stage       | `BASEBALL.RAW.BASEBALL_STAGE`                             |

---

## Setup Order

1. Create the S3 bucket
2. Create an IAM policy granting Snowflake the minimum required S3 permissions
3. Create an IAM role with an initial (placeholder) trust policy
4. Attach the S3 policy to the IAM role
5. Create the Snowflake storage integration (see `01_storage_integration.sql`)
6. Retrieve Snowflake's generated IAM values via `DESC INTEGRATION`
7. Update the IAM role's trust policy with those Snowflake-provided values
8. Create the Snowflake external stage (see `02_stage_and_file_formats.sql`)
9. Verify connectivity with `LIST @BASEBALL.RAW.BASEBALL_STAGE`

---

## Step 1 — S3 Bucket

Create the bucket in the AWS console or CLI. No public access is needed.

```
Bucket name:  <BUCKET_NAME>
Region:       (your preferred region, e.g. us-east-1)
Public access: blocked (all four checkboxes checked)
Versioning:   optional
```

### Expected S3 Layout

After uploading parquet snapshots, the bucket should contain:

```
s3://<BUCKET_NAME>/
├── payroll/
│   └── parquet/
│       ├── players.parquet
│       ├── summary.parquet
│       └── other_payments.parquet
├── batting/
│   └── batting.parquet
└── pitching/
    └── pitching.parquet
```

Upload from local `data/parquet/` using the AWS CLI or console, preserving this structure.
Example CLI upload:

```
aws s3 cp data/parquet/players.parquet        s3://<BUCKET_NAME>/payroll/parquet/players.parquet
aws s3 cp data/parquet/summary.parquet        s3://<BUCKET_NAME>/payroll/parquet/summary.parquet
aws s3 cp data/parquet/other_payments.parquet s3://<BUCKET_NAME>/payroll/parquet/other_payments.parquet
aws s3 cp data/parquet/batting.parquet        s3://<BUCKET_NAME>/batting/batting.parquet
aws s3 cp data/parquet/pitching.parquet       s3://<BUCKET_NAME>/pitching/pitching.parquet
```

---

## Step 2 — IAM Policy (S3 Access)

Create an IAM policy (inline or managed) and attach it to the role created in Step 3.
This policy grants Snowflake the minimum permissions needed to read from the bucket.

**Policy name (suggested):** `snowflake-baseball-s3-read`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::<BUCKET_NAME>", "arn:aws:s3:::<BUCKET_NAME>/*"]
    }
  ]
}
```

If you ever need Snowflake to write back to S3 (e.g. for UNLOAD / external tables), add:

- `s3:PutObject`
- `s3:DeleteObject`

For this project (read-only ingest), the four actions above are sufficient.

---

## Step 3 — IAM Role (Initial Trust Policy)

Create an IAM role named `<IAM_ROLE_NAME>`.

During creation, Snowflake's IAM user ARN is not yet known, so use a placeholder trust policy
that restricts assumption to your own account root. You will replace this in Step 7.

**Initial trust policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<AWS_ACCOUNT_ID>:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "PLACEHOLDER"
        }
      }
    }
  ]
}
```

After creating the role, attach the S3 policy from Step 2 to it.

Copy the role ARN — you will need it in `01_storage_integration.sql`:

```
arn:aws:iam::<AWS_ACCOUNT_ID>:role/<IAM_ROLE_NAME>
```

---

## Step 4 — Create the Snowflake Storage Integration

Run `01_storage_integration.sql` in Snowflake (as `ACCOUNTADMIN`), with your role ARN and
bucket name filled in.

Then run:

```sql
DESC INTEGRATION s3_baseball_analytics_integration;
```

From the output, copy two values:

| Property                   | Description                                         |
| -------------------------- | --------------------------------------------------- |
| `STORAGE_AWS_IAM_USER_ARN` | The AWS IAM user Snowflake uses to assume your role |
| `STORAGE_AWS_EXTERNAL_ID`  | The external ID Snowflake uses for role assumption  |

These are Snowflake-generated and unique to your account. They are not secrets (no passwords or
keys), but they should only be shared with trusted operators of this account.

---

## Step 5 — Update IAM Role Trust Policy

Go to the IAM role `<IAM_ROLE_NAME>` in the AWS console and replace the trust policy with the
values retrieved from `DESC INTEGRATION` above.

**Final trust policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "AWS": "<STORAGE_AWS_IAM_USER_ARN>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<STORAGE_AWS_EXTERNAL_ID>"
        }
      }
    }
  ]
}
```

Replace `<STORAGE_AWS_IAM_USER_ARN>` and `<STORAGE_AWS_EXTERNAL_ID>` with the actual values
from the `DESC INTEGRATION` output.

The `ExternalId` condition is critical — it prevents the
[confused deputy problem](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html)
where another Snowflake customer could attempt to use your role.

---

## Step 6 — Create Stage and Verify

Run `02_stage_and_file_formats.sql` in Snowflake to create the external stage.

Then verify connectivity:

```sql
LIST @BASEBALL.RAW.BASEBALL_STAGE;
```

You should see the parquet files listed. If you get an error, check:

1. The trust policy has been saved with the correct ARN and external ID (not the placeholder).
2. The S3 policy is attached to the role and covers both the bucket ARN and the `/*` ARN.
3. `STORAGE_ALLOWED_LOCATIONS` in the integration matches the bucket URL exactly.
4. The stage URL matches the bucket name.

---

## Security Notes

- No AWS access keys or secret keys are used. Authentication is entirely via IAM role assumption
  (STS `AssumeRole`). Snowflake holds no long-lived AWS credentials for this integration.
- The `ExternalId` condition in the trust policy is mandatory — do not remove it.
- `STORAGE_ALLOWED_LOCATIONS` in the Snowflake integration is scoped to this bucket only.
- If the Snowflake account is migrated or the integration is recreated, the `STORAGE_AWS_IAM_USER_ARN`
  and `STORAGE_AWS_EXTERNAL_ID` will change and the trust policy must be updated again.

---

## Re-validation After Changes

If any of the following change, re-run the verification steps above:

- IAM role ARN or trust policy is modified
- Snowflake storage integration is dropped and recreated
- S3 bucket name or prefix changes
- Snowflake account is migrated to a new region or org
