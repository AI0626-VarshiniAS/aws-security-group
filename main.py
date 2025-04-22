import subprocess
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
import boto3
import argparse

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

# def wait_for_jobs_to_complete(timeout_minutes=30):
#     """Simulates waiting for other jobs to complete with a timeout."""
#     start_time = datetime.now()
#     end_time = start_time + timedelta(minutes=timeout_minutes)
#     while datetime.now() < end_time:
#         time.sleep(10)
#         remaining = end_time - datetime.now()
#         logging.info(f"⌛ Waiting for jobs to complete... Time left: {remaining}")
    
#     logging.info("🕒 Timeout reached. Proceeding with cleanup.")
#     return True

def parse_args():
    parser = argparse.ArgumentParser(description='Modify security group by adding and removing IP.')
    parser.add_argument('--security-group-id', required=True, help='AWS Security Group ID')
    parser.add_argument('--port', required=True, help='Port to open (e.g., 22)')
    parser.add_argument('--protocol', default='tcp', help='Protocol (default: tcp)')
    parser.add_argument('--description', default='GitHub Action IP', help='Description for rule')
    parser.add_argument('--region', required=True, help='AWS region (e.g., us-east-1)')
    parser.add_argument('--to-port', help='Optional: ToPort if different from FromPort')
    parser.add_argument('--wait-minutes', type=int, default=30, help='How long to wait before removing IP')

    return parser.parse_args()

def main():
    args = parse_args()
    print("printing arguments",args)

    add_ip_to_sg(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)
    
    # wait_for_jobs_to_complete(timeout_minutes=args.wait_minutes)

    remove_ip_from_sg(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)

if __name__ == '__main__':
    main()
