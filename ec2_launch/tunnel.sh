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
wait_seconds=5 # seconds between polls for the public IP to populate (keeps it from hammering their API)
port=22 # the SSH tunnel port you want
key_location="~/lambda/ericscrape1.pem" # your private key -- http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair
user=ec2-user # the EC2 linux user name
user_data=scrape_movies.sh
# END SETTINGS

# --------------------- you shouldn't have to change much below this ---------------------

# private
connect ()
{
	ssh -oStrictHostKeyChecking=no -ND $port -i $key_location $user@$ip
}

# private
getip ()
{
	ip=$(aws ec2 describe-instances | grep PublicIpAddress | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}")
}

# public
start ()
{
	echo "Starting instance..."
	aws ec2 run-instances --image-id $imageid --count 1 --instance-type $instance_type --key-name $key_name --security-group-ids $security_group --user-data $user_data > /dev/null 2>&1

	# wait for a public ip
	while true; do

		echo "Waiting $wait_seconds seconds for IP..."
		sleep $wait_seconds
		getip
		if [ ! -z "$ip" ]; then
			break
		else
			echo "Not found yet. Waiting for $wait_seconds more seconds."
			sleep $wait_seconds
		fi

	done

	echo "Found IP $ip - Starting tunnel on port $port"

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
	getip

	connect
}

# public
instruct ()
{
	echo "Please provide an argument: start, stop, resume"
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
	help|*)
		instruct
		;;
esac
