#!/bin/bash

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
# END SETTINGS

# --------------------- you shouldn't have to change much below this ---------------------



#allocate=$(aws ec2 allocate-address | grep PublicIp | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}")
#assignment=$(aws ec2 associate-address -i )

# public
info ()
{
	instance_id=$(aws ec2 run-instances --image-id $imageid --count 1 --instance-type $instance_type --key-name $key_name --security-group-ids $security_group --user-data $user_data --output text --query 'Instances[*].InstanceId' )
	echo "This is the instance_id $instance_id"


}

# private
connect ()
{
	ldns=$(aws ec2 describe-instances --instance-ids $instance_id --output text --query 'Reservations[].Instances[].PublicDnsName')
	echo "the dns is $ldns"

	ssh -o StrictHostKeyChecking=no -i $key_location $user@$ldns
}

# private
getip ()
{
	#allocate=
	ip=$(aws ec2 describe-instances | grep PublicIpAddress | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}")
}

# public
start ()
{
	echo "Starting instance..."
	instance_id=$(aws ec2 run-instances --image-id $imageid --count 1 --instance-type $instance_type --key-name $key_name --security-group-ids $security_group --user-data file://scrape_movies1.txt --output text --query 'Instances[*].InstanceId' )
	echo "the instance id is $instance_id"
	#script I found on stack overflow  --NEEDS TO CHANGE
	aws ec2 create-tags --resources $instance_id --tags "Key=Name, Value=$AMIname"
	#delay until AWS says instance is running
	echo "sleeping half a minute"

	sleep 30
	echo "done sleeping"

	ip_address=$(aws ec2 describe-instances --instance-ids $instance_id --output text --query 'Reservations[*].Instances[*].PrivateIpAddress')
	echo "got the ip_address: $ip_address"
	sleep 5
	echo "gonna sleep for another half a minute"
	sleep 30
	echo "better try to connect now"
	connect
}


# public
stop ()
{
	instance=$(aws ec2 describe-instances | grep InstanceId | grep -E -o "i\-[0-9A-Za-z]+")

	aws ec2 terminate-instances --instance-ids $instance
}

# public
resume ()
{
	#getip

	connect
}



# public
instruct ()
{
	echo "Please provide an argument: start, stop, resume, info"
}


#-------------------------------------------------------

# "main"
case "$1" in
	start)
		start
		;;
	resume)
		resume
		;;
	stop)
		stop
		;;
	info)
		info
		;;
	help|*)
		instruct
		;;
esac
