import boto3
import argparse
import sys

def get_ip():
    import requests
    return requests.get("https://api.ipify.org").text

def add_ip(ec2, sg_id, port, protocol, description, to_port):
    ip = get_ip()
    ip_range = f"{ip}/32"
    ip_permissions = [{
        'IpProtocol': protocol,
        'FromPort': int(port),
        'ToPort': int(to_port) if to_port else int(port),
        'IpRanges': [{
            'CidrIp': ip_range,
            'Description': description
        }]
    }]
    ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=ip_permissions)
    print(f"✅ IP {ip_range} added to Security Group {sg_id}")

def remove_ip(ec2, sg_id, port, protocol, description, to_port):
    ip = get_ip()
    ip_range = f"{ip}/32"
    ip_permissions = [{
        'IpProtocol': protocol,
        'FromPort': int(port),
        'ToPort': int(to_port) if to_port else int(port),
        'IpRanges': [{
            'CidrIp': ip_range,
            'Description': description
        }]
    }]
    ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=ip_permissions)
    print(f"❌ IP {ip_range} removed from Security Group {sg_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--security-group-id', required=True)
    parser.add_argument('--port', required=True)
    parser.add_argument('--protocol', default='tcp')
    parser.add_argument('--description', default='GitHub Action IP')
    parser.add_argument('--region', required=True)
    parser.add_argument('--to-port')
    parser.add_argument('--action', required=True, choices=['add', 'remove'])

    args = parser.parse_args()

    ec2 = boto3.client('ec2', region_name=args.region)

    if args.action == 'add':
        add_ip(ec2, args.security_group_id, args.port, args.protocol, args.description, args.to_port)
    else:
        remove_ip(ec2, args.security_group_id, args.port, args.protocol, args.description, args.to_port)
