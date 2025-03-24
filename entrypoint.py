import boto3
import json
import os
import subprocess
import sys

def fetch_secrets(secret_name, region_name="en-north-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(get_secret_value_response["SecretString"])
    return secret

def set_env_vars(secrets: dict):
    for key, value in secrets.items():
        os.environ[key] = value

def main():
    django_env = os.getenv("DJANGO_ENV", "development")
    print(f"Running in {django_env} mode")

    if django_env == "production":
        secret_name = os.getenv("DJANGO_AWS_SECRET_NAME")
        if not secret_name:
            print("Error: 'DJANGO_AWS_SECRET_NAME' not set. Exiting.")
            sys.exit(1)

        region_name = os.getenv("AWS_REGION", "eu-north-1")
        try:
            secrets = fetch_secrets(secret_name, region_name)
            set_env_vars(secrets)
            print(f"Loaded production secrets: {list(secrets.keys())}")
        except Exception as e:
            print(f"Failed to fetch secrets: {e}")
            sys.exit(1)
    else:
        print("Development mode: using local environment variables / .env")

    # Continue running Django command or gunicorn
    cmd = sys.argv[1:]
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True) # nosec

if __name__ == "__main__":
    main()