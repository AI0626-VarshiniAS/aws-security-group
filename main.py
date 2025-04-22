import subprocess
import sys
import logging
import requests
import boto3
import argparse
import os

# Function to install packages if they are not already installed
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
install('boto3')
install('requests')

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_public_ip():
    """Fetches the public IP of the machine."""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json().get('ip')
    except requests.RequestException as e:
        logging.error(f"Error fetching public IP: {e}")
        return None

def add_ip_to_sg(security_group_id, port, protocol, description, region, to_port=None):
    """Adds the public IP to the security group."""
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
        logging.info(f"✅ Added IP {public_ip} to security group {security_group_id}")

    except Exception as e:
        logging.error(f"Error adding IP: {e}")

def remove_ip_from_sg(security_group_id, port, protocol, description, region, to_port=None):
    """Removes the public IP from the security group."""
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
        logging.info(f"✅ Removed IP {public_ip} from security group {security_group_id}")

    except Exception as e:
        logging.error(f"Error removing IP: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description='Modify security group by adding and removing IP.')
    parser.add_argument('--security-group-id', required=True, help='AWS Security Group ID')
    parser.add_argument('--port', required=True, help='Port to open (e.g., 22)')
    parser.add_argument('--protocol', default='tcp', help='Protocol (default: tcp)')
    parser.add_argument('--description', default='GitHub Action IP', help='Description for rule')
    parser.add_argument('--region', required=True, help='AWS region (e.g., us-east-1)')
    parser.add_argument('--to-port', help='Optional: ToPort if different from FromPort')
    parser.add_argument('--action', required=True, choices=['add', 'remove'], help="Action to perform: 'add' or 'remove' IP")
    parser.add_argument('--account-id', required=True, help='AWS Account ID')

    return parser.parse_args()

def main():
    args = parse_args()
    print("Arguments:", args)

    # Fetch AWS credentials dynamically based on the provided account-id
    account_id = args.account_id
    aws_access_key = os.getenv(f'AWS_ACCESS_KEY_ID_{account_id}')
    aws_secret_key = os.getenv(f'AWS_SECRET_ACCESS_KEY_{account_id}')

    if not aws_access_key or not aws_secret_key:
        logging.error(f"Error: AWS credentials for account ID {account_id} not found in environment variables.")
        return

    # Set the AWS credentials as environment variables for boto3
    os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key

    # Proceed with the action based on the input
    if args.action == 'add':
        add_ip_to_sg(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)
    elif args.action == 'remove':
        remove_ip_from_sg(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)

if __name__ == '__main__':
    main()
    