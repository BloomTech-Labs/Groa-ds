How to get the credentials for running EC2 Instance Script


#### First you want to take the following steps:

```
* Go to aws.amazon.com
* From the My Account dropdown menu (top right of screen) Select security credentials
* Sign into your account
* Under "Access keys for CLI, SDK, & API access"
* Select Create access key
* Download your public and secret keys
* Name the keys [yourname]_rootkey.csv
* Create a folder named '[yourname]AWSCredentials'

```

#### Once you have your Security Keys you will want to establish a security group
#### for the EC2 instances by:

```
* Go to aws.amazon.com
* From the Services dropdown select EC2
* Under Network & Security Select Security Groups
* Create new security group
* Name the security group 'Letterboxd Scrape'
* In the description field put today's date
* In the bottom left corner select the button to Add New Rule
* Populate the new rule with the following options:
Type: SSH
Protocol: TCP
Port Range: 22
Source: Anywhere
IP range: 0.0.0.0/0,::/0
Description: SSH for letterboxd scrapers
* Do not change the outbound rules.
* In the bottom right click the 'Create' button
*Copy the Group ID for your newly created Security Group
* Save it to a text file you name '[yourname]SecurityGroup'
* Save this text file in the '[yourname]AWSCredentials' folder we created earlier
```

#### Finally you go to Key Pairs, which is also under Network & Security and
#### you create a new key pair by:

```
* Selecting Create Key Pair
* Leave File format as pem
* Name the keypair '[yourname]letterboxdscrape'
* Select create key pair
* Save that .pem file to the '[yourname]AWSCredentials' folder we created earlier
```

Now all that's left to do is zip that [yourname]AWSCredentials folder and dm it
to me via slack.
