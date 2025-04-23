import argparse
import os
import logging
import boto3
import requests

logging.basicConfig(level=logging.INFO)

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org?format=json').json()['ip']
    except Exception as e:
        logging.error(f"Unable to fetch public IP: {e}")
        return None

def get_credentials_from_env(account_id):
    access_key = os.getenv(f"AWS_ACCESS_KEY_{account_id}")
    secret_key = os.getenv(f"AWS_SECRET_ACCESS_KEY_{account_id}")

    if not access_key or not secret_key:
        logging.error(f"❌ Missing credentials for account ID: {account_id}")
        exit(1)

    return access_key, secret_key

def manage_ip(action, ec2, sg_id, port, protocol, description, to_port):
    ip = get_public_ip()
    if not ip:
        logging.error("❌ Could not get public IP.")
        return

    ip_permissions = {
        'IpProtocol': protocol,
        'FromPort': int(port),
        'ToPort': int(to_port) if to_port else int(port),
        'IpRanges': [{'CidrIp': f'{ip}/32', 'Description': description}]
    }

    try:
        if action == 'add':
            ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[ip_permissions])
            logging.info(f"✅ Added IP {ip} to SG {sg_id}")
        else:
            ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[ip_permissions])
            logging.info(f"✅ Removed IP {ip} from SG {sg_id}")
    except Exception as e:
        logging.error(f"❌ Error modifying SG: {e}")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--security-group-id', required=True)
    parser.add_argument('--port', required=True)
    parser.add_argument('--protocol', default='tcp')
    parser.add_argument('--description', default='GitHub runner')
    parser.add_argument('--to-port')
    parser.add_argument('--action', required=True, choices=['add', 'remove'])
    parser.add_argument('--account-id', required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    logging.info(f"🔐 Using credentials for account: {args.account_id}")

    access_key, secret_key = get_credentials_from_env(args.account_id)
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=args.aws_region
    )
    ec2 = session.client('ec2')
    manage_ip(args.action, ec2, args.security_group_id, args.port, args.protocol, args.description, args.to_port)

if __name__ == '__main__':
    main()
