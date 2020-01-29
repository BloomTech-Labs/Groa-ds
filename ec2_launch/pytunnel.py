import aws2 as aws
import awscli


# Start/stop an EC2 instance to use as a ssh tunnel
# requires the aws package locally -- sudo apt-get install awscli
#
# usage: ./tunnel.sh start (spin up EC2 and create the tunnel)
#        ./tunnel.sh stop (terminate the EC2 instance to save money)
#        ./tunnel.sh resume (in case your tunnel is interrupted but the EC2 instance is still running)

# CHANGE THE PARAMETERS BELOW

imageid=ami-062f7200baf2fa504 # this is an Amazon Linux AMI, but you can change it to whatever you want
instance_type=t2.micro
key_name=$EC2_INSTANCE_KEY # your keypair name -- instantiated in the env file http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html
security_group=sg-0fb23b3d00c3d354a # your security group -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html
wait_seconds=30 # seconds between polls for the public IP to populate (keeps it from hammering their API)
port=23453 # the SSH tunnel port you want
key_location="scraperboi.pem" # your private key -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair
user="ec2-user" # the EC2 linux user name
user_data=file://scrape_movies0.txt
