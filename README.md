<div style="display: flex; align-items: center;">
  <img src="logo.png" alt="Logo" width="50" height="50" style="margin-right: 10px;"/>
  <span style="font-size: 2.2em;">Get AWS Secrets</span>
</div>

![GitHub Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Get%20AWS%20Secrets%20S3-blue?logo=github)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GitHub Action to retrieve secrets from AWS Secrets Manager. Supports setting default values, and preset secrets.

See more [GitHub Actions by DevOpspolis](https://github.com/marketplace?query=devopspolis&type=actions)

---
## 📚 Table of Contents

- [✨ Features](#features)
- [📥 Inputs](#inputs)
- [📤 Outputs](#outputs)
- [📦 Usage](#usage)
- [🚦 Requirements](#requirements)
- [🔧 Troubleshooting](#troubleshooting)
- [🧑‍⚖️ Legal](#legal)

---

<!-- trunk-ignore(markdownlint/MD033) -->
<a id="features"></a>
## ✨ Features

- Retrieves secrets from AWS Secrets Manager
- Supports filtering specific keys from secrets
- Provides default values for missing keys
- Merges preset secrets with retrieved values
- Automatically resolves short IAM role names to full ARNs
- Configurable AWS region support
- Returns secrets in JSON format for easy consumption
- Multiple invocations supports GitHub Action chaining

---
<!-- trunk-ignore(markdownlint/MD033) -->
<a id="inputs"></a>
## 📥 Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `secrets` | Space delimited list of AWS Secrets Manager secret names to retrieve | true | — |
| `secrets-filter` | Space delimited list of keys to include from the retrieved secrets (filters out other keys) | false | `''` |
| `role` | IAM role ARN or short name to assume for secret retrieval | false | — |
| `aws-region` | AWS region to use (falls back to AWS_REGION, AWS_DEFAULT_REGION, then us-east-1) | false | — |
| `default-value` | Default value to assign to filtered keys that are not found in secrets | false | `''` |
| `preset-secrets` | JSON string containing preset key-value pairs to merge with retrieved secrets | false | `'{}'` |

---
<!-- trunk-ignore(markdownlint/MD033) -->
<a id="outputs"></a>
## 📤 Outputs

| Name | Description |
|------|-------------|
| `secrets` | Retrieved secrets as JSON object with key-value pairs |
| `secrets-filter` | Space-separated list of secret keys returned |
| `secrets-count` | Number of secrets returned |

---

<!-- trunk-ignore(markdownlint/MD033) -->
<a id="usage"></a>
## 📦 Usage

### Syntax
````yaml
uses: devopspolis/get-aws-secrets@main
with:
  [inputs]
````

### Example 1 – Basic secret retrieval

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Get secrets
        id: secrets
        uses: devopspolis/get-aws-secrets@main
        with:
          secrets: myapp/database myapp/api-keys

      - name: Use secrets
        run: |
          echo "Database URL: ${{ fromJson(steps.secrets.outputs.secrets).DB_URL }}"
          echo "API Key: ${{ fromJson(steps.secrets.outputs.secrets).API_KEY }}"
```

### Example 2 – Filtered secrets with defaults

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Get filtered secrets
        id: secrets
        uses: devopspolis/get-aws-secrets@main
        with:
          secrets: myapp/config myapp/database
          secrets-filter: DB_URL API_KEY DEBUG_MODE
          default-value: "NOT_SET"

      - name: Use filtered secrets
        run: |
          echo "Retrieved ${{ steps.secrets.outputs.secrets-count }} secrets"
          echo "Keys: ${{ steps.secrets.outputs.secrets-filter }}"
```

### Example 3 – Using preset secrets and IAM role

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Get secrets with presets
        id: secrets
        uses: devopspolis/get-aws-secrets@main
        with:
          secrets: myapp/production
          role: github-secrets-reader
          aws-region: us-west-2
          preset-secrets: |
            {
              "ENVIRONMENT": "production",
              "LOG_LEVEL": "info",
              "FEATURE_FLAG": "enabled"
            }
```

### Example 4 – Complete workflow with secret injection

```yaml
name: Deploy Application
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions
          aws-region: us-east-1

      - name: Get application secrets
        id: app-secrets
        uses: devopspolis/get-aws-secrets@main
        with:
          secrets: myapp/database myapp/api-keys myapp/config
          secrets-filter: DB_URL API_KEY REDIS_URL DEBUG_MODE
          default-value: "undefined"

      - name: Deploy with secrets
        run: |
          # Use secrets in deployment
          docker run -d \
            -e DB_URL="${{ fromJson(steps.app-secrets.outputs.secrets).DB_URL }}" \
            -e API_KEY="${{ fromJson(steps.app-secrets.outputs.secrets).API_KEY }}" \
            -e REDIS_URL="${{ fromJson(steps.app-secrets.outputs.secrets).REDIS_URL }}" \
            -e DEBUG_MODE="${{ fromJson(steps.app-secrets.outputs.secrets).DEBUG_MODE }}" \
            myapp:latest
```

## Secret Structure

AWS Secrets Manager secrets should be stored as JSON objects:

**Example secret `myapp/database`:**
```json
{
  "DB_URL": "postgresql://user:pass@host:5432/db",
  "DB_USER": "myapp_user",
  "DB_PASSWORD": "secure_password",
  "DB_MAX_CONNECTIONS": "100"
}
```

**Example secret `myapp/api-keys`:**
```json
{
  "API_KEY": "abcd1234567890",
  "STRIPE_KEY": "sk_test_...",
  "SENDGRID_API_KEY": "SG...."
}
```

## IAM Role Resolution

The action supports both full ARN and short role names:

- **Full ARN**: `arn:aws:iam::123456789012:role/github-secrets-reader`
- **Short name**: `github-secrets-reader` (requires `AWS_ACCOUNT_ID` environment variable)

```yaml
env:
  AWS_ACCOUNT_ID: "123456789012"
steps:
  - name: Get secrets
    uses: devopspolis/get-aws-secrets@main
    with:
      secrets: myapp/config
      role: github-secrets-reader  # Will be resolved to full ARN
```

## Region Resolution

The action resolves AWS region in the following order:

1. `aws-region` input parameter
2. `AWS_REGION` environment variable
3. `AWS_DEFAULT_REGION` environment variable
4. Default fallback: `us-east-1`

## Output Usage

The action returns secrets in multiple formats for flexibility:

```yaml
- name: Get secrets
  id: secrets
  uses: devopspolis/get-aws-secrets@main
  with:
    secrets: myapp/config

- name: Use secrets (JSON)
  run: |
    echo "All secrets: ${{ steps.secrets.outputs.secrets }}"
    echo "Specific secret: ${{ fromJson(steps.secrets.outputs.secrets).API_KEY }}"

- name: Use secrets (filtered keys)
  run: |
    echo "Available keys: ${{ steps.secrets.outputs.secrets-filter }}"
    echo "Secret count: ${{ steps.secrets.outputs.secrets-count }}"
```

---
<!-- trunk-ignore(markdownlint/MD033) -->
<a id="requirements"></a>
## 🚦 Requirements

### Required AWS Permissions

The GitHub workflow must provide AWS credentials with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:*"
    }
  ]
}
```

### Additional permissions if using IAM roles:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole"
      ],
      "Resource": "arn:aws:iam::*:role/*"
    }
  ]
}
```

### AWS Credentials Setup

Use the official AWS configure credentials action:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions
    aws-region: us-east-1
```

## Error Handling

The action provides clear error messages for common issues:

- **Secret not found**: Lists the missing secret name and region
- **Invalid JSON**: Reports JSON parsing errors in preset secrets
- **Missing permissions**: AWS credential and permission errors
- **Role resolution**: Errors when AWS_ACCOUNT_ID is missing for short role names

---
<!-- trunk-ignore(markdownlint/MD033) -->
<a id="troubleshooting"></a>
## 🔧 Troubleshooting

### Secret Not Found

If you get a "Secret not found" error:

1. Verify the secret name is correct
2. Check that the secret exists in the specified region
3. Ensure your AWS credentials have access to the secret
4. Confirm the secret is not disabled or deleted

### Permission Denied

If you get permission errors:

1. Verify your IAM role/user has `secretsmanager:GetSecretValue` permission
2. Check that resource ARNs in your policy match your secret ARNs
3. Ensure the role trust policy allows your GitHub Actions to assume it

### Region Issues

If secrets aren't found in the expected region:

1. Explicitly set the `aws-region` input
2. Verify your secrets exist in the target region
3. Check AWS_REGION environment variables

---
<!-- trunk-ignore(markdownlint/MD033) -->
<a id="legal"></a>
## 🧑‍⚖️ Legal
The MIT License (MIT)

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/devopspolis/get-aws-secrets).