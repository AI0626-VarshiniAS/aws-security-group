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

def modify_security_group(security_group_id, port, protocol, description, region, to_port=None):
    """Modifies the security group by adding or removing an IP."""
    try:
        # Initialize boto3 EC2 client
        ec2 = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
            aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY'
        )

        # Get public IP
        public_ip = get_public_ip()
        if not public_ip:
            logging.error("Could not retrieve public IP.")
            return

        # Define permission to check
        ip_permission = {
            'IpProtocol': protocol,
            'FromPort': int(port),
            'ToPort': int(to_port) if to_port else int(port),
            'IpRanges': [{'CidrIp': f'{public_ip}/32', 'Description': description}]
        }

        # Fetch current security group rules
        response = ec2.describe_security_groups(GroupIds=[security_group_id])
        group = response['SecurityGroups'][0]
        existing_permissions = group.get('IpPermissions', [])

        ip_found = False
        for permission in existing_permissions:
            if permission['IpProtocol'] == protocol and permission['FromPort'] == int(port):
                for ip_range in permission['IpRanges']:
                    if ip_range.get('CidrIp') == f'{public_ip}/32':
                        ip_found = True
                        break

        if ip_found:
            # If the IP is found, remove it
            ec2.revoke_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[ip_permission]
            )
            logging.info(f"The IP {public_ip} has been removed from the security group {security_group_id}.")
        else:
            # If the IP is not found, add it
            ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[ip_permission]
            )
            logging.info(f"The IP {public_ip} has been added to the security group {security_group_id}.")

    except Exception as e:
        logging.error(f"Error: {e}")

def wait_for_jobs_to_complete(timeout_minutes=30):
    """Simulate waiting for other jobs to complete with a timeout."""
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=timeout_minutes)
    while datetime.now() < end_time:
        # Sleep for a few seconds before checking again (simulate job completion check)
        time.sleep(10)
        logging.info(f"Waiting for jobs to complete. Time left: {end_time - datetime.now()}")
    
    logging.info("Timeout reached. Proceeding with IP removal if needed.")
    return True

# Parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Modify security group by adding/removing IP.')
    parser.add_argument('--security-group-id', required=True, help='AWS Security Group ID')
    parser.add_argument('--port', required=True, help='The port which you want to allow')
    parser.add_argument('--protocol', default='tcp', help='Protocol for the rule (default: tcp)')
    parser.add_argument('--description', default='GitHub Action IP', help='Description of the IP permission')
    parser.add_argument('--region', required=True, help='AWS Region (e.g., us-east-1)')
    parser.add_argument('--to-port', help='To port for the rule (optional)')

    return parser.parse_args()

# Example usage
def main():
    args = parse_args()

    # Modify security group (add/remove IP)
    modify_security_group(args.security_group_id, args.port, args.protocol, args.description, args.region, args.to_port)

    # Wait for the jobs to finish (timeout after 30 minutes)
    wait_for_jobs_to_complete(timeout_minutes=30)

    # After waiting for the jobs, ensure the IP is removed (if added earlier)
    logging.info("Completed all tasks, the IP should be removed if it was added.")
    modify_security_group(args.security_group_id, args.port, args.protocol, args.description, args.region, to_port=None)

if __name__ == '__main__':
    main()
