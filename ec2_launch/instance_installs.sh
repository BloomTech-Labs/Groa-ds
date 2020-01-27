#!/bin/bash
set -e

function usage
{
  echo
  echo "$(basename $0) spools up a new ec2 instance"
  echo
  echo "usage: $(basename $0) -k key [[[-a ip_address] [-s script]] | [-h]]"
  echo "       -a, --ami          : the Amazon Machine Image (AMI) name"
  echo "       -d, --disks        : Comma separated list of block device mappings"
  echo "                          :   e.g. '/dev/sda1=:8:false,/dev/sda1=:1:true'"
  echo "                          :   (see ec2-run-instances -h option --block-device-mapping for format)"
  echo "       -h, --help         : displays the information you're reading now"
  echo "       -i, --ip-address   : the IP Address to assign to the new instance"
  echo "       -s, --script       : the shell script to run after the instance is created"
  echo "       -t, --instance-type: e.g. t1.micro, m1.small, m1.large, etc."
  echo
}

if [ ! $EC2_HOME ] || [ ! $EC2_INSTANCE_KEY ]; then
  echo
  echo "An EC2_HOME environment variable set to the EC2 installation directory (usually"
  echo "~/.ec2) and an EC2_INSTANCE_KEY environment variable set to the EC2 keypair "
  echo "name must be defined. The EC2 instance key must reside in the directory specified"
  echo "in EC2_HOME. You will need to create the environment variable based on the requirements"
  echo "of your particular Operating System."
  echo
  exit 1
fi

# Authorize TCP, SSH & ICMP for default Security Group
#ec2-authorize default -P icmp -t -1:-1 -s 0.0.0.0/0
#ec2-authorize default -P tcp -p 22 -s 0.0.0.0/0

# Loop through command line params and capture values
while [ "$1" != "" ]; do
  case $1 in
    -i | --ip-address )    shift
                           IP_ADDRESS=$1
                           ;;
    -s | --script )        shift
                           INSTALL_SCRIPT=$1
                           ;;
    -h | --help )          usage
                           exit
                           ;;
    -a | --ami )           shift
                           AMI=$1
                           ;;
    -d | --disks )         shift
                           DISKS=$1
                           ;;
    -t | --instance-type ) shift
                           INSTANCE_TYPE=$1
                           ;;
    * )                    usage
                           exit 1
  esac

  shift
done

echo

if [ ! $AMI ]; then
  AMI="ami-062f7200baf2fa504"
  echo "No AMI specified. Using Amazon Linux 2 AMI (HVM), SSD Volume Type (ami-062f7200baf2fa504) by default..."
else
  echo "Using specified ami: ($AMI)"
fi

if [ ! $DISKS ]; then
  # --block-device-mapping ...:false to leave the disk image around after terminating the instance
  BLOCK_DEVICE_MAPPINGS='--block-device-mapping "/dev/sda1=:8:true"'
  echo "No disks specified. Using 8GB image not deleted on instance termination by default..."
else
  IFS=$','
  for disk in $DISKS; do BLOCK_DEVICE_MAPPINGS="--block-device-mapping \"$disk\" $BLOCK_DEVICE_MAPPINGS"; done
  unset IFS
  echo "Using specified disk mappings: ($BLOCK_DEVICE_MAPPINGS)"
fi

if [ ! $INSTANCE_TYPE ]; then
  INSTANCE_TYPE="t2.micro"
  echo "No instance-type specified. Using t2.micro by default..."
else
  echo "Using specified instance-type: ($INSTANCE_TYPE)"
fi

echo
echo "Starting your new instance. Please wait..."

if [ $INSTALL_SCRIPT ]; then
  echo "The script $INSTALL_SCRIPT will be run once the instance is created."
  SCRIPT_PARAM="--user-data-file $INSTALL_SCRIPT"
fi

MAX_SECONDS_TO_WAIT=181
SECONDS_TO_ADD=5

# Create new instance
EC2_RUN_RESULT=$(ec2-run-instances --instance-type $INSTANCE_TYPE --group default --key $EC2_INSTANCE_KEY $BLOCK_DEVICE_MAPPINGS --instance-initiated-shutdown-behavior stop $SCRIPT_PARAM $AMI)

INSTANCE_NAME=$(echo ${EC2_RUN_RESULT} | sed 's/RESERVATION.*INSTANCE //' | sed 's/ .*//')

SECONDS_TO_WAIT=0

echo

while [ $MAX_SECONDS_TO_WAIT -gt $SECONDS_TO_WAIT ] && ! ec2-describe-instances $INSTANCE_NAME | grep -q "running"
do
  SECONDS_TO_WAIT=$(( $SECONDS_TO_WAIT + $SECONDS_TO_ADD ))
  echo "$INSTANCE_NAME not running. Waiting $SECONDS_TO_WAIT seconds before checking again..."
  sleep $(echo $SECONDS_TO_WAIT)s
done

if [ $MAX_SECONDS_TO_WAIT -lt $SECONDS_TO_WAIT ]; then
  echo "Instance $INSTANCE_NAME is taking too long to enter the running state. Exiting..."
  exit 1
fi

echo
echo "Instance $INSTANCE_NAME is now running."

DESCRIBE_INSTANCE=$(ec2-describe-instances $INSTANCE_NAME)
INSTANCE_FQDN=$(echo ${DESCRIBE_INSTANCE} | sed -E 's/RESERVATION.*ami-.{9}//' | sed -E 's/\ .*//')

if [ $IP_ADDRESS ]; then
  echo "Associating it with IP Address $IP_ADDRESS..."
  ec2-associate-address $IP_ADDRESS -i $INSTANCE_NAME
fi

# Sleep for a bit... ssh seems to fail if started too soon.
echo "Please wait..."
sleep 20s

# SSH details for my BRAND NEW EC2 INSTANCE! WooHoo!!!
echo "You can ssh into your new instance with the following command:"
echo "ssh -o StrictHostKeyChecking=no -i $EC2_HOME/$EC2_INSTANCE_KEY.pem ec2-user@$INSTANCE_FQDN"
