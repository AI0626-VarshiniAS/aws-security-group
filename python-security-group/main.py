import subprocess
import sys
import logging
import requests
import boto3
import argparse
import os
from dotenv import load_dotenv

# Function to install packages if they are not already installed
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
install('boto3')
install('requests')
install('python-dotenv')

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json().get('ip')
    except requests.RequestException as e:
        logging.error(f"Error fetching public IP: {e}")
        return None

def load_credentials_from_env(account_id, env_file="val.env"):
    load_dotenv(env_file)
    access_key_var = f"AWS_ACCESS_KEY_{account_id}"
    secret_key_var = f"AWS_SECRET_ACCESS_KEY_{account_id}"

    access_key = os.getenv(access_key_var)
    secret_key = os.getenv(secret_key_var)

    if not access_key or not secret_key:
        raise ValueError(f"Missing AWS credentials for account {account_id}")

    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    logging.info(f"Loaded AWS credentials for account {account_id}")

def add_ip_to_sg(security_group_id, port, protocol, description, region, to_port=None):
    try:
        ec2 = boto3.client('ec2', region_name=region)
        public_ip = get_public_ip()
        if not public_ip:
            logging.error("Could not retrieve public IP.")
            return

        ip_permission = {
            'IpProtocol': protocol,
            'FromPort': int(port),
            'ToPort': int(to_port) if to_port else int(port),
            'IpRanges': [{'CidrIp': f'{public_ip}/32', 'Description': description}]
        }

        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[ip_permission]
        )
        logging.info(f"Added IP {public_ip} to security group {security_group_id}")

    except Exception as e:
        logging.error(f"Error adding IP: {e}")

def remove_ip_from_sg(security_group_id, port, protocol, description, region, to_port=None):
    try:
        ec2 = boto3.client('ec2', region_name=region)
        public_ip = get_public_ip()
        if not public_ip:
            logging.error("Could not retrieve public IP.")
            return

        ip_permission = {
            'IpProtocol': protocol,
            'FromPort': int(port),
            'ToPort': int(to_port) if to_port else int(port),
            'IpRanges': [{'CidrIp': f'{public_ip}/32', 'Description': description}]
        }

        ec2.revoke_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[ip_permission]
        )
        logging.info(f"Removed IP {public_ip} from security group {security_group_id}")

    except Exception as e:
        logging.error(f"Error removing IP: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description='Modify AWS Security Group IP rules.')
    parser.add_argument('--account', required=True, help='Account ID for credentials')
    parser.add_argument('--security-group-id', required=True, help='Security Group ID')
    parser.add_argument('--port', required=True, help='Port to open/close')
    parser.add_argument('--protocol', default='tcp', help='Protocol (default: tcp)')
    parser.add_argument('--description', default='GitHub Action IP', help='Description')
    parser.add_argument('--region', required=True, help='AWS region')
    parser.add_argument('--to-port', help='Optional to_port')
    parser.add_argument('--action', required=True, choices=['add', 'remove'], help='Action to perform')

    return parser.parse_args()

def main():
    args = parse_args()
    load_credentials_from_env(args.account)

    if args.action == 'add':
        add_ip_to_sg(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)
    elif args.action == 'remove':
        remove_ip_from_sg(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)

if __name__ == '__main__':
    main()
