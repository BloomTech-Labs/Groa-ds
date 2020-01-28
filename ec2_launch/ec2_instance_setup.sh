#!/bin/bash

# Authorize TCP, SSH & ICMP for default Security Group
#aws2 ec2-authorize default -P icmp -t -1:-1 -s 0.0.0.0/0
#aws2 ec2-authorize default -P tcp -p 22 -s 0.0.0.0/0

# The Static IP Address for this instance:
IP_ADDRESS=$(cat ip_address)

# Create new t1.micro instance using ami-af7e2eea (64 bit Using Amazon Linux 2 AMI (HVM), SSD Volume Type)
# using the default security group and a 8GB EBS datastore as /dev/sda1.
# EC2_INSTANCE_KEY is an environment variable containing the name of the instance key.
# --block-device-mapping ...:false to leave the disk image around after terminating instance (removed)
EC2_RUN_RESULT=$(aws2 ec2 run-instances --instance-type t2.micro --region us-east-1 --security-group-ids default --key-name $EC2_INSTANCE_KEY --instance-initiated-shutdown-behavior stop --user-data-file scrape_movies.sh --image-id ami-062f7200baf2fa504)

INSTANCE_NAME=$(echo ${EC2_RUN_RESULT} | sed 's/RESERVATION.*INSTANCE //' | sed 's/ .*//')

times=0
echo
while [ 500 -gt $times ] && ! aws2 ec2 describe-instances $INSTANCE_NAME | grep -q "running"
do
  times=$(( $times + 1 ))
  echo Attempt $times at verifying $INSTANCE_NAME is running...
done

echo

if [ 500 -eq $times ]; then
  echo Instance $INSTANCE_NAME is not running. Exiting...
  exit
fi

ec2-associate-address $IP_ADDRESS -i $INSTANCE_NAME

echo
echo Instance $INSTANCE_NAME has been created and assigned static IP Address $IP_ADDRESS
echo

# Since the server signature changes each time, remove the server's entry from ~/.ssh/known_hosts
# You may not need to do this if you're using a Reserved Instance?
ssh-keygen -R $IP_ADDRESS

# SSH INTO NEW EC2 INSTANCE
ssh -i $EC2_HOME/$EC2_INSTANCE_KEY.pem ec2-user@$IP_ADDRESS
