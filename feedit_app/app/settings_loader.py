import json
import os

import boto3


def load_secrets():
    if os.getenv("DJANGO_ENV") != "production":
        return

    secret_name = os.getenv("DJANGO_AWS_SECRET_NAME")
    region_name = os.getenv("AWS_REGION", "eu-north-1")

    if not secret_name:
        raise Exception("DJANGO_AWS_SECRET_NAME not set")

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secrets = json.loads(get_secret_value_response["SecretString"])

    for key, value in secrets.items():
        os.environ.setdefault(key, value)  # only sets if not already present
