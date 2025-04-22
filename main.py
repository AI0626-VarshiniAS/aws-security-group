import os
import boto3
import logging
import argparse

# Function to retrieve AWS credentials from environment variables or secrets
def get_aws_credentials(account_id):
    aws_access_key_id = os.getenv(f'AWS_ACCESS_KEY_ID_{account_id}')
    aws_secret_access_key = os.getenv(f'AWS_SECRET_ACCESS_KEY_{account_id}')

    if not aws_access_key_id or not aws_secret_access_key:
        logging.error(f"AWS credentials for account ID {account_id} not found.")
        raise ValueError(f"AWS credentials for account ID {account_id} not found.")
    
    return aws_access_key_id, aws_secret_access_key

def modify_security_group(account_id, security_group_id, port, protocol, action, description, region, to_port=None):
    try:
        aws_access_key_id, aws_secret_access_key = get_aws_credentials(account_id)
        
        # Set AWS credentials using boto3
        ec2 = boto3.client(
            'ec2', 
            region_name=region, 
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        # Define IP permission
        ip_permission = {
            'IpProtocol': protocol,
            'FromPort': int(port),
            'ToPort': int(to_port) if to_port else int(port),
            'IpRanges': [{'CidrIp': f'0.0.0.0/0', 'Description': description}]  # Example: Using 0.0.0.0/0 for public IP
        }

        if action == 'add':
            ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[ip_permission]
            )
            logging.info(f"✅ Added IP to security group {security_group_id}")
        
        elif action == 'remove':
            ec2.revoke_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[ip_permission]
            )
            logging.info(f"✅ Removed IP from security group {security_group_id}")
        else:
            logging.error("Invalid action specified. Use 'add' or 'remove'.")
    except Exception as e:
        logging.error(f"Error modifying security group: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modify security group by adding/removing IP.')
    parser.add_argument('--account-id', required=True, help='Account ID')
    parser.add_argument('--security-group-id', required=True, help='AWS Security Group ID')
    parser.add_argument('--port', required=True, help='Port (e.g., 22)')
    parser.add_argument('--protocol', default='tcp', help='Protocol (default: tcp)')
    parser.add_argument('--action', required=True, choices=['add', 'remove'], help="Action to perform: 'add' or 'remove'")
    parser.add_argument('--description', default='GitHub Action IP', help='Description for rule')
    parser.add_argument('--region', required=True, help='AWS Region (e.g., us-east-1)')
    parser.add_argument('--to-port', help='Optional: ToPort if different from FromPort')

    args = parser.parse_args()

    # Run the function with the provided arguments
    modify_security_group(args.account_id, args.security_group_id, args.port, args.protocol, args.action, args.description, args.region, args.to_port)
