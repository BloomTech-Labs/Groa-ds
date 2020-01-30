import aws2 as aws
import awscli
from decouple import config
import boto3
import pprint
import datetime
import time
import requests
#import paramiko


import awsutils

# Start/stop a set number of EC2 instances to use as a ssh tunnel
# requires above packages to be pip installed locally
# usage: ./tunnel.sh start (spin up EC2 and create the tunnel)
#        ./tunnel.sh stop (terminate the EC2 instance to save money)
#        ./tunnel.sh resume (in case your tunnel is interrupted but the EC2 instance is still running)
# Check the output by going to "vim /var/log/cloud-init-output.log"
# CHANGE THE PARAMETERS BELOW

imageid = "ami-062f7200baf2fa504" # this is an Amazon Linux AMI, but you can change it to whatever you want
instance_type = "t2.micro"
instance_quantity = 30
key_name = config("EC2_INSTANCE_KEY") # your keypair name -- instantiated in the env file http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html
security_group = ["sg-0fb23b3d00c3d354a"] # your security group -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html
wait_seconds = 30 # seconds between polls for the public IP to populate (keeps it from hammering their API)
port = 23453 # the SSH tunnel port you want
key_location = "scraperboi.pem" # your private key -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair
user = "ec2-user" # the EC2 linux user name
#user_data = "file://scrape_movies0.txt"
ec2 = boto3.resource('ec2')
session = awsutils.get_session('us-east-1')
client = session.client('ec2')
resource = session.resource('ec2')
#client = paramiko.SSHClient()
# --------------------- Below is a quick rundown of what each part does ---------------------

"""
#return the region name for the currently running boto3 session
def get_session(region):
    return boto3.session.Session(region_name=region)

#instantiate instance when already started
demo = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['demo-instance']}])


#find the instance ID
instance_id = demo['Reservations'][0]['Instances'][0]['InstanceId']

#instantiate the instance
instance = resource.Instance(instance_id)

#starts an instance
client.start_instances(InstanceIds=[instance_id])

#stops an instance
client.stop_instances(InstanceIds=[instance_id])

#creating an image
date = datetime.datetime.utcnow().strftime('%Y%m%d')
name = f"InstanceID_{instance_id}_Image_Backup_{date}"
client.create_image(InstanceId=instance_id, Name=name)

#alternative method to create image
image = instance.create_image(Name=name + '_2')

#create an EC2 instance from an image ID
client.run_instances(ImageId='ami-081c72fa60c8e2d58', MinCount=1, MaxCount=1, InstanceType='t3.micro')

#terminating instance
"""
# --------------------- Below is the code for launching instances ---------------------


def launch(quantity):
    """
    Creates a set number of EC2 instances with the given file parameters.
    """
    for i in range(quantity):
        instance = client.run_instances(
        ImageId=imageid,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=security_group,
        UserData=f'file://scrape_movies2.txt',
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Scraper', 'Value': f'{i}'}]}]
        )

        print("Taking a quick sleep after making scraper", i)
        time.sleep(15)

#        find_name = client.describe_instances(Filters=[{'Name': 'Scraper', 'Values': [f'{i}']}])
#        inid = find_name['Reservations'][0]['Instances'][0]['InstanceId']
#        print("The InstanceId for this scraper is:", iid)
#        time.sleep(2)
#        print("Taking another little snooze")
#        time.sleep(10)
#        pdns = find_name['Reservations'][0]['Instances'][0]['PublicDnsName']
#        print("Here's the PublicDNS:", pdns)



if __name__ == "__main__":
    num = int(input("How many instances would you like to make?"))
    launch(num)
