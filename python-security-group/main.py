import boto3
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# AWS EC2 client setup
ec2 = boto3.client('ec2')

# Config settings (These can be passed as environment variables or hardcoded)
SECURITY_GROUP_IDS = ['sg-xxxxxxxxxxxxxxxxx']  # Replace with your SG IDs
PORT = 22  # Port you want to add the IP for
PROTOCOL = 'tcp'  # Protocol (tcp/udp)
DESCRIPTION = 'Temporary IP access'  # Description for the IP range
TO_PORT = 22  # If applicable, otherwise set to False

# Get public IP of the machine
def get_public_ip():
    return requests.get("https://checkip.amazonaws.com").text.strip()

# Add the public IP to the security group
def add_ip_to_sg(sg_id, ip, port, to_port, protocol, description):
    response = ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{
            'IpProtocol': protocol,
            'FromPort': port,
            'ToPort': to_port,
            'IpRanges': [{'CidrIp': f'{ip}/32', 'Description': description}]
        }]
    )
    logging.info(f"✅ Added IP {ip} to SG {sg_id}")
    return response

# Remove the public IP from the security group
def remove_ip_from_sg(sg_id, ip, port, to_port, protocol):
    response = ec2.revoke_security_group_ingress(
        GroupId=sg_id,
        CidrIp=f'{ip}/32',
        IpProtocol=protocol,
        FromPort=port,
        ToPort=to_port
    )
    logging.info(f"🧹 Removed IP {ip} from SG {sg_id}")
    return response

def main():
    # Get the public IP of the current machine
    public_ip = get_public_ip()
    logging.info(f"Using public IP: {public_ip}")

    # Adding IP to each Security Group
    for sg_id in SECURITY_GROUP_IDS:
        try:
            # Add the IP to the security group
            add_ip_to_sg(sg_id, public_ip, PORT, TO_PORT if TO_PORT else PORT, PROTOCOL, DESCRIPTION)

            # Your script's work goes here (you can replace this with your actual deployment or task)
            logging.info("🚀 Running the main task... (This is where your deployment logic goes)")

            # After your work is done, remove the IP from the security group
            remove_ip_from_sg(sg_id, public_ip, PORT, TO_PORT if TO_PORT else PORT, PROTOCOL)
        
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            break  # If you want to break the loop on failure

if __name__ == "__main__":
    main()
