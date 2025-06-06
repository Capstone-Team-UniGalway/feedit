import json
import os
import subprocess
import sys

import boto3


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

    # ✅ Print storage backend for verification
    from django.core.files.storage import default_storage

    print(f"✅ Active storage backend: {default_storage.__class__}")

    # Continue running Django command or gunicorn
    cmd = sys.argv[1:]
    # If no command is passed, run migrate + gunicorn
    if not cmd:
        print("No command passed. Running migrate and gunicorn.")
        subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)
        subprocess.run(
            ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi:application"], check=True
        )
    else:
        print(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
