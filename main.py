import os
import logging
import argparse
from dotenv import load_dotenv
import boto3
import requests

# Load the .env file
load_dotenv(dotenv_path=".env")

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json().get('ip')
    except Exception as e:
        logging.error(f"Error fetching public IP: {e}")
        return None

def get_aws_session(account_id, region):
    access_key = os.getenv(f"AWS_ACCESS_KEY_ID_{account_id}")
    secret_key = os.getenv(f"AWS_SECRET_ACCESS_KEY_{account_id}")

    if not access_key or not secret_key:
        raise Exception(f"Missing credentials for account: {account_id}")

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    return session

def add_ip(session, sg_id, port, protocol, description):
    ip = get_public_ip()
    if not ip:
        return

    ec2 = session.client("ec2")
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": protocol,
                "FromPort": int(port),
                "ToPort": int(port),
                "IpRanges": [{"CidrIp": f"{ip}/32", "Description": description}]
            }
        ]
    )
    logging.info(f"✅ Added {ip} to SG {sg_id}")

def remove_ip(session, sg_id, port, protocol, description):
    ip = get_public_ip()
    if not ip:
        return

    ec2 = session.client("ec2")
    ec2.revoke_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": protocol,
                "FromPort": int(port),
                "ToPort": int(port),
                "IpRanges": [{"CidrIp": f"{ip}/32", "Description": description}]
            }
        ]
    )
    logging.info(f"✅ Removed {ip} from SG {sg_id}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-group-id", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--protocol", default="tcp")
    parser.add_argument("--description", default="GitHub runner IP")
    parser.add_argument("--region", required=True)
    parser.add_argument("--action", choices=["add", "remove"], required=True)
    parser.add_argument("--account-id", required=True)
    args = parser.parse_args()

    session = get_aws_session(args.account_id, args.region)

    if args.action == "add":
        add_ip(session, args.security_group_id, args.port, args.protocol, args.description)
    else:
        remove_ip(session, args.security_group_id, args.port, args.protocol, args.description)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
