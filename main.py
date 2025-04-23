import os
import boto3
import argparse
import logging
import requests

logging.basicConfig(level=logging.INFO)

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json().get('ip')
    except requests.RequestException as e:
        logging.error(f"Error fetching public IP: {e}")
        return None

def set_boto3_session(account_id, region):
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not access_key or not secret_key:
        logging.error(f"❌ Missing credentials for account ID: {account_id}")
        exit(1)

    logging.info(f"🔐 Using credentials for account: {account_id}")
    return boto3.client('ec2', region_name=region,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

def modify_sg(ec2, security_group_id, port, protocol, description, action, to_port=None):
    public_ip = get_public_ip()
    if not public_ip:
        logging.error("❌ Could not retrieve public IP.")
        return

    ip_permission = {
        'IpProtocol': protocol,
        'FromPort': int(port),
        'ToPort': int(to_port) if to_port else int(port),
        'IpRanges': [{'CidrIp': f'{public_ip}/32', 'Description': description}]
    }

    try:
        if action == 'add':
            ec2.authorize_security_group_ingress(GroupId=security_group_id, IpPermissions=[ip_permission])
            logging.info(f"✅ Added IP {public_ip} to security group {security_group_id}")
        elif action == 'remove':
            ec2.revoke_security_group_ingress(GroupId=security_group_id, IpPermissions=[ip_permission])
            logging.info(f"✅ Removed IP {public_ip} from security group {security_group_id}")
    except Exception as e:
        logging.error(f"❌ Error modifying IP: {e}")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--account-id', required=True)
    parser.add_argument('--security-group-id', required=True)
    parser.add_argument('--port', required=True)
    parser.add_argument('--action', required=True, choices=['add', 'remove'])
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--protocol', default='tcp')
    parser.add_argument('--description', default='GitHub runner')
    parser.add_argument('--to-port')
    return parser.parse_args()

def main():
    args = parse_args()
    ec2 = set_boto3_session(args.account_id, args.aws_region)
    modify_sg(ec2, args.security_group_id, args.port, args.protocol, args.description, args.action, args.to_port)

if __name__ == '__main__':
    main()
