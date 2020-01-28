#!/bin/bash

# function to display help information
function usage
{
  echo
  echo "terminate_instance.sh [image_name]"
  echo
  echo "removes the server's entry from known_hosts and terminates the instance"
  echo
}

if [ ! $1 ]; then
  usage
  exit 1
fi

echo "Getting $1's Fully Qualified Domain Name..."

DESCRIBE_INSTANCE=$(aws2 ec2 describe-instances $1)
INSTANCE_FQDN=$(echo ${DESCRIBE_INSTANCE} | sed -E 's/RESERVATION.*ami-.{9}//' | sed -E 's/\ .*//')

echo "Removing $INSTANCE_FQDN from known_hosts..."
ssh-keygen -R $INSTANCE_FQDN

echo "Terminating $INSTANCE_FQDN..."
aws2 ec2 terminate-instances $1
