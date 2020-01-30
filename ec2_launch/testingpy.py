import aws2 as aws
import awscli
from decouple import config
import boto3
import pprint
import datetime

import awsutils

# Start/stop a set number of EC2 instances to use as a ssh tunnel
# requires these packages locally -- pip3 install awscli
#                                   -- pip3 install boto3
#                                   -- pip3 install python-decouple
#                                   -- pip3 install aws2
#                                   -- pip3 install pprint
#                                   -- pip3 install datetime
#
# usage: ./tunnel.sh start (spin up EC2 and create the tunnel)
#        ./tunnel.sh stop (terminate the EC2 instance to save money)
#        ./tunnel.sh resume (in case your tunnel is interrupted but the EC2 instance is still running)

# CHANGE THE PARAMETERS BELOW

imageid = "ami-062f7200baf2fa504" # this is an Amazon Linux AMI, but you can change it to whatever you want
instance_type = "t2.micro"
instance_quantity = 30
key_name = config("EC2_INSTANCE_KEY") # your keypair name -- instantiated in the env file http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html
security_group = "sg-0fb23b3d00c3d354a" # your security group -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html
wait_seconds = 30 # seconds between polls for the public IP to populate (keeps it from hammering their API)
port = 23453 # the SSH tunnel port you want
key_location = "scraperboi.pem" # your private key -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair
user = "ec2-user" # the EC2 linux user name
user_data = "file://scrape_movies0.txt"
ec2 = boto3.resource('ec2')
session = awsutils.get_session('us-east-1')
client = session.client('ec2')
resource = session.resource('ec2')
# --------------------- Below is a quick rundown of what each part does ---------------------


#return the region name for the currently running boto3 session
def get_session(region):
    return boto3.session.Session(region_name=region)


demo = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['demo-instance']}])


#find the instance ID
instance_id = demo['Reservations'][0]['Instances'][0]['InstanceId']

#starts an instance
client.start_instances(InstanceIds=[instance_id])

#stops an instance
client.stop_instances(InstanceIds=[instance_id])

#creating an image instance
date = datetime.datetime.utcnow().strftime('%Y%m%d')
name = f"InstanceID_{instance_id}_Image_Backup_{date}"
client.create_image(InstanceId=instance_id, Name=name)

#alternative method to create image
image = instance.create_image(Name=name + '_2')

#create an EC2 instance from an image ID
client.run_instances(ImageId='ami-081c72fa60c8e2d58', MinCount=1, MaxCount=1, InstanceType='t3.micro')

#terminating instance

# --------------------- Below is a quick rundown of what each part does ---------------------


def launch(quantity):
    """
    Creates a set number of EC2 instances with the given file parameters.
    """
    for i in self.quantity:
        client.run_instances(
        ImageId=imageid,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=security_group,
        )

    instance_id = aws ec2 run-instances
    ImageId=imageid,
    MinCount=1,
    MaxCount=1,
    InstanceType=instance_type,
    KeyName=key_name,
    SecurityGroupIds=security_group,
     --output text --query 'Instances[*].InstanceId'
    instance_id =
    print("done")
