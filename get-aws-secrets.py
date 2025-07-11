#!/usr/bin/env python3
# File: get-aws-secrets.py

import os
import sys
import json
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='[get-aws-secrets.py] %(message)s')

SECRETS = os.environ.get("SECRETS", "")
SECRETS_FILTER = os.environ.get("SECRETS_FILTER", "")
DEFAULT_VALUE = os.environ.get("DEFAULT_VALUE", "")
PRESET_SECRETS = os.environ.get("PRESET_SECRETS", "{}")
    
def initialize_secrets_with_defaults(filter_keys, default_value=''):
    """Initialize secrets with default values for specified keys"""
    secrets = {}
    if filter_keys:
        for key in filter_keys:
            secrets[key] = default_value
            # logging.info(f"Set default value for key: {key}")
    return secrets

def parse_preset_secrets(filter_keys=''):
    """Parse preset secrets from JSON string"""
    preset = {}
    try:
        if not PRESET_SECRETS or PRESET_SECRETS.strip() == "":
            return {}
        if filter_keys:
            tmp_preset = json.loads(PRESET_SECRETS)
            for key in filter_keys:
                if key in tmp_preset:
                    preset[key] = tmp_preset[key]
        else:
            preset = json.loads(PRESET_SECRETS)
        if isinstance(preset, dict):
            logging.info(f"Loaded {len(preset)} preset secrets")
            return preset
        else:
            logging.warning("Preset secrets is not a JSON object, ignoring")
            return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in preset-secrets: {e}")
        return {}

def fetch_secrets(secrets_list, filter_keys=None):
    """Fetch secrets from AWS Secrets Manager"""
    logging.info(f"Fetching secrets from {secrets_list}")
    
    # Get region from environment or default
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    
    # Create client with explicit region
    client = boto3.client("secretsmanager", region_name=region)
    all_secrets = {}
    loaded_secrets = []
    try:
        # Get and process each of the secrets
        secret_ids = [s.strip() for s in secrets_list.replace(",", " ").split()]
        
        for sid in secret_ids:
            if not sid:
                continue
            logging.info(f"Retrieving secret: {sid}")     
            try:
                response = client.get_secret_value(SecretId=sid)
                secrets = json.loads(response["SecretString"])
                for key, value in secrets.items():
                    # Filter keys if specified
                    if filter_keys and key not in filter_keys:
                        continue 
                    all_secrets[key] = value
                    loaded_secrets.append(key)
                    logging.info(f"Retrieved secret: {key}")    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    logging.error(f"Secret '{sid}' not found in region '{region}'")
                raise
    except Exception as e:
        logging.error(f"Error fetching secrets: {e}")
        raise
    return all_secrets

def set_github_output(name, value):
    """Set GitHub Actions output variable"""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            if isinstance(value, dict):
                # Properly escape JSON for GitHub Actions output
                json_str = json.dumps(value, separators=(',', ':'))
                f.write(f"{name}={json_str}\n")
            else:
                f.write(f"{name}={value}\n")

def main():
    all_secrets = {}
    
    try:  
        # Parse filter keys if provided
        filter_keys = None
        if SECRETS_FILTER:
            filter_keys = [k.strip() for k in SECRETS_FILTER.replace(",", " ").split() if k.strip()]
            logging.info(f"Filtering to keys: {filter_keys}")
            
        # Step 1: Initialize with default values for filtered keys
        if filter_keys and 'DEFAULT_VALUE' in os.environ:
            all_secrets = initialize_secrets_with_defaults(filter_keys, DEFAULT_VALUE)
            
        # Step 2: Load preset secrets
        all_secrets.update(parse_preset_secrets(filter_keys))
        
        # Step 3: Fetch secrets from AWS (this will overwrite defaults and presets)
        if SECRETS:
            aws_secrets = fetch_secrets(SECRETS, filter_keys)
            all_secrets.update(aws_secrets)
        else:
            logging.warning("SECRETS not set. Skipping AWS secret fetch.")

        # Step 4: Extract the actual secret keys (excluding metadata)
        # secret_keys = [k for k in all_secrets.keys() if k != "SECRETS_LOADED"]
        all_secrets = dict(sorted(all_secrets.items()))
        secret_keys = [k for k in all_secrets.keys()]
        secrets_filter_str = " ".join(sorted(secret_keys))
        
        # Step 5: Set GitHub Actions outputs
        secrets_count = len(secrets_filter_str.split())
        set_github_output("secrets", all_secrets)
        set_github_output("secrets-filter", secrets_filter_str)
        set_github_output("secrets-count", secrets_count)
        
        # For local testing, also print the results
        if not os.environ.get("GITHUB_OUTPUT"):
            logging.info(f"secrets: {json.dumps(all_secrets, indent=2)}")
            logging.info(f"secrets-filter: {secrets_filter_str}")
            logging.info(f"secrets-count: {secrets_count}")
        
        # logging.info("Secret fetching completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    