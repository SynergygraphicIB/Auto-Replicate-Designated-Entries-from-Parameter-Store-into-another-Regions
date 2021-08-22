# Replicate Parameter Store Entries into another Regions using an automated workflow:
This is an open-source solution to deploy **AutoReplication** of Parameter Store Entries using `CloudTrail` and route the deployment event through `Cloudwatch Events`, and `EventBrigdge`,` across regions if it is the case to an endpoint - a `lambda function` to `replicate parameter entries` at the moment of creation or thru a scheduled event in CloudWatch which rewrites the value. 
Hence an Entry created in a central parameter store, say in US-EAST-1, it is replicated in US-EAST-2. If it is already in existence in US-EAST-2 then it is updated.

### PreFlight Check
1. Intermedial to advance level in Python. So, you can adapt and customized the `auto-replicate-parameter-store.py` files to your need an use cases.
2. Basic to intermedial level in json to edit json rules in `EventBridge Rules` to modify it if needed to your use case, since we give granular limited access to AWS resources.
3. One AWS Region known as the "the Central or *Receiver Region"* to deploy the parameters to be replicated. Here is where we deploy **auto-replicate-parameter-store**.
6. In the designated Central Region you choose for the Parameter Store Entries you will need the following
    A. `Eventbridge` rules in the central region in order to pass the "PutParameter" events from `cloudtrail` to the lambda function as an endpoint.

## List of AWS Resources used in the Auto Replicate Parameter Entries workflow
1. IAM
2. Lambda
3. CloudWatch
4. CloudTrail
5. SSM Parameter Store

## List of Programming languages used
1. Python 3.9

## Required IAM Roles and Policies
In this case `Identity and Access Management (IAM)` is a global element, so do not worry in what region you are in at the moment of loggin in. Though some AWS Services are global like this one and `S3` some others like `EventBridge`, `CloudWatch`, and `Lambda` is regional; therefore, be sure you are in us-east-1 (N. Virginia) for most of the purposes of this project. 
We need one role **auto-replicate-parameter-store-role** with limited granular permissions to interact with other AWS Services such as: IAM, KMS, EC2, SSM, CloudWatch Logs for this project

And we need to attach the following policy to the role
**policy.json** - IAM Policy to authorize *auto-replicate-parameter-store-role* to replicate Parameter Store Entries
See `policy.json`
or copy paste from here...
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeParameters",
                "ec2:DescribeRegions"
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "kms:Encrypt",
                "ssm:ListTagsForResource",
                "kms:ReEncryptTo",
                "ssm:GetParametersByPath",
                "ssm:GetParameters",
                "kms:GenerateDataKeyPair",
                "ssm:GetParameter"
            ],
            "Resource": [
                "arn:aws:kms:*:111111111111:key/75fcc799-de1b-42a9-9a12-a23b31111111111",
                "arn:aws:ssm:*:111111111111:parameter/*"
            ]
        }
    ]
}
```
### Amazon EventBridge and CloudWatch
**EventRule.json** - This rule filters create or launch events coming from `AWS API Call via CloudTrail` that start with the event name "PutParameter" which is the one create Paramter Store entries.
See `EventRule.json`
or copy paste from here...

```json
{
  "source": [
    "aws.ssm"
  ],
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventSource": [
      "ssm.amazonaws.com"
    ],
    "eventName": [
      "PutParameter"
    ]
  }
}
```

Note: sometimes when creating complex custom rules such as when using prefix feature it is necessary to create them in EventBridge or to update the very same rules. If it is done CloudWatch directly it may not not work. Hence, we best configure the rules in EventBridge even though the end result is also shown in CloudWatch. 

### AWS Lambda

**auto-replicate-parameter-store** - Lambda function that we deploy in the *Designated Region* or in our case the us-east-1 region to replicate . It is triggered by a "PutParameter" coming from CloudWatch. 

### Let us check this solution's architecture and workflow
A Parameter Store Entry is deployed either by using the console or the AWS SDK for Python (Boto3). Yet, all replication is going to be done by the **auto-replicate-parameter-store** lambda function in us-east-1. The New Parameter Store Entry with the tag replicate/yes or replicate/us-east-2 generates an event metadata; the timestamp, who was the creator, ARN of the creator, etc, but the one we really need is the tag containing the key/value pair = replicate/yes.

Then, `CloudWatch` in us-east-1 filters the creation event based on **EventRule.json** This rule looks for any event that has "PutParameter", it matches the event  and sends the metadata to the lambda funcion **auto-replicate-parameter-store** as an endpoint.
 
Thus, the lambda function checks if the value of replicate tag is set to yes. If true **auto-replicate-parameter-store** lambda funtion is fired and proceeds to replicate the entry into whatever regions are set in the Environment variables in the Lambda function.

In Summary, The purpose of this pipeline is to centralize the control Parameter Store Entries from a centralized Parameter Store in a designated Region. In this way is easier to manage and monitor entries that are to be used across regions it the Parameter Store


## Steps to Create the Pipeline to do the Auto-Replicate Parameter Store

### 1. Log in into you account designated as Receiver Account 
Log in to Account ID 111111111111. This is the account we are going to use to centralized the **Autotagging** in the Organization. This AWS Service is global.

### 2 Setting up the primary Role "MasterAutoTaggingLambda" in ReceiverAccount
First, we create an **"AssumeLinkedRolePolicy"** to allow AutoTaggingMasterLambda role in receiver account  to assume any role named **ExecuteAutoTaggingLambda** in any *Linked account*:

a.- Be sure you are in *Receiver Account* 111111111111
b.- At the console screen go to services and type in the text box `"IAM"` or under All
    ```Services > Security, Identity, & Compliance > IAM```
c.- In `Identity and Access Managment (IAM) menu > go to Policies` and click `"Create policy"` button
d.- Click Create policy next.
e.- In Create policy window select JSON tab. Click and copy-paste the following policy and click the "Next: tags" button:

```json
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::*:role/ExecuteAutoTaggingLambda"
    }
}
```

h.- Click "Next: Review" button
i.- In Review policy window in Name type **"AssumeLinkedRolePolicy"**
j.- In Description type "Rule to enable **AutoTaggingMasterLambda** Role to assume any role named "AutoTaggingExecuteLambda" in any Linked Account" and click "Create policy". 

![alt text](https://github.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/blob/main/img/1.png?raw=true)





#### Create "MasterAutoTaggingLambda" role in Receiver Account
a.- Be sure you are in `Receiver Account` 111111111111
b.- At the console screen go to services and type in the text box `"IAM"` or under All services > Security, Identity, & Compliance > IAM
d.- In Create Role window > Under "Select type of trusted entity" keep AWS service as your choice
e.- In "Choose a use case" select "Lambda" and click "Next: Permissions" button
f.- In next window, under Attach Permissions policies in the search box type "lambdabasic"
g.- Checkmark the AWS managed policy **"AWSLambdaBasicExecutionRole"**
h.- Under Create policy clear the Search box 
i- Click Filter policies and checkmark "Customer managed"
j.- Scroll down and checkmark the Customer managed policy **"AssumeLinkedRolePolicy"**
k.-  Click "Next:Tags" button and click "Next: Review" button too
l.- Under Review, in Role name `*` type **"MasterAutoTaggingLambda"** 
m.- In Role description type "Resource Role to give permission to lambda autotagging function in *receiver account* to assume roles named **"ExecuteAutoTaggingLambda"** in linked account with AWS STS service". 
Observe that in Trusted entities you got AWS service: lambda.amazonaws.com and two policies attached to the role
n.- Click "Create Role Button"

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/2.png)

Is noteworthy to say you should keep the same role name **"ExecuteAutoTaggingLambda"** in every new or existing linked accounts in your organization that you want to include in the Auto-tagging pipeline.

### 3 Setting up a Role in Linked Account
Create a role in *Linked Account* that has enough permissions to execute lambda to add tags to resources. 
Follow the steps:
**Create a Policy **"ExecuteAutoTaggingLambdaPolicy"** to allow **ExecuteAutoTaggingLambda** role in Linked Account to enable Lambda to tag resources. Remember this role will be assumed by **"MasterAutoTaggingLambda"** in Receiver Account:
a.- Be sure you are in *Linked Account* 222222222222
b.- At the console screen go to services and type in the text box `"IAM"` or under All
    ```Services > Security, Identity, & Compliance > IAM```
c.- In `Identity and Access Managment (IAM) menu > go to Policies` and click `"Create policy"` button
d.- Click Create policy next.
e.- In Create policy window select JSON tab. Click and paste the following policy and click the "Next: tags" button:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BasicWritePermissionstoCloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Sid": "AutoTaggerforAWSResources",
            "Effect": "Allow",
            "Action": [
                "resource-explorer:*",
                "tag:*",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:GetLogEvents",
                "iam:*Tags",
                "iam:Tag*",
                "iam:Untag*",
                "cloudtrail:*Tags",
                "*:*Tags",
                "s3:*Tagging",
                "s3:*Tags",
                "sns:TagResource",
                "sns:UntagResource",
                "sqs:TagQueue",
                "sqs:UntagQueue",
                "cloudformation:UpdateStackSet",
                "cloudformation:CreateChangeSet",
                "cloudformation:UpdateStackInstances",
                "codepipeline:CreatePipeline",
                "codepipeline:TagResource",
                "codepipeline:UntagResource",
                "codepipeline:CreateCustomActionType",
                "codepipeline:ListTagsForResource",
                "codepipeline:GetPipeline",
                "codepipeline:PutWebhook",
                "codebuild:UpdateProject",
                "codebuild:BatchGetProjects",
                "ssm:GetParameters",
                "ssm:ListTagsForResource",
                "ssm:AddTagsToResource",
                "ssm:RemoveTagsFromResource",
                "ssm:GetParametersByPath",
                "mediastore:TagResource",
                "mediastore:UntagResource",
                "cloudformation:TagResource",
                "cloudformation:UpdateStack",
                "cloudformation:UntagResource",
                "cloudformation:UpdateTerminationProtection",
                "lambda:*tag*"
            ],
            "Resource": "*"
        }
    ]
}
```

h.- Click "Next: Review" button.
i.- In Review policy window in Name type **"ExecuteAutoTaggingLambdaPolicy"**
j.- In Description type "Policy to enable **ExecuteAutoTaggingLambda** Role to tag newly deployed resources" and click "Create policy"

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/3.png)

#### Create ExecuteAutoTaggingLambda role in Linked Account
a.- Be sure you are in *Receiver Account* 222222222222
b.- At the console screen go to services and type in the text box `"IAM"` or under All services > Security, Identity, & Compliance > IAM
d.- In Create Role window > Under "Select type of trusted entity" keep AWS service as your choice
e.- In "Choose a use case" select "Lambda" and click "Next: Permissions" button
![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/4.png)
f- Click Filter policies and checkmark "Customer managed"
g.- Scroll down and checkmark the Customer managed policy **"ExecuteAutoTaggingLambdaPolicy"**
h.-  Click "Next:Tags" button and click "Next: Review" button too
i.- Under Review, in Role name `*` type **ExecuteAutoTaggingLambda.** 
j.- In Role description type "Resource Role to give permission to lambda autotagging function in *receiver account* to tag resources deployed in this Linked Account". 
Observe that in Trusted entities you got AWS service: lambda.amazonaws.com and two policies attached to the role.
k.- Click "Create Role Button"

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/5.png)

Is noteworthy to say you should keep the same role name **"ExecuteAutoTaggingLambda"** in every new linked accounts in your organization so as not to keep adding new policies into the Receiver Account

#### Modify ExecuteAutoTaggingLambda role trust policy 
We have to modify the trust policy to enable **"MasterAutoTaggingLambda"** in Receiver Account assumes **ExecuteAutoTaggingLambda** in Linked Account
a. Search for the Role we just created. In the text box under "Create role" button type "ExecutAauto
b. Click ExecuteAutoTaggingLambda
c. In Summary window you can see all related info about the role. Click the "Trust relationships" tab and click "Edit trust relationship" button
d. In Edit Trust Relationship window you can customize trust relationships by editing the following access control policy document with the following json:

```json
 {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/MasterAutoTaggingLambda"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
Note: Edit the 111111111111 Account number with your Receiver Account ID

e. CLick "Update Trust Policy" button and next stept


## 4. Deploy Autotagging Lambda Function in Receiver Account

We set our lambda function in virginia region or us-east-1. This is the endpoint for any deployment or creation event happening in any region in any account that is configured in the pipeline for **Auto-tagging* and in this lambda function. 

Create a **AutoTagging** lambda function with the console:

a.- First, be sure you are in Receiver Account in us-east-1 . In the console click the services tab and look for Lamdba under (It seems repetive, but it is easy to be in the wrong account and fail to do the settings)
```
All services > Compute > Lambda or just type lambda in the text box. then hit Lambda
```
b.- In the AWS lambda window go to Functions.
c. Click the "Create function" buttom.
d. You will the following options to create your function Author from scratch, Use blueprint, Container Image, and Browse serverless app repository, choose Author from scratch.
e. In Function name type **"AutoTagging"** or any name you choose to, in Runtime look for Python 3.8
f.- In Permissions - click Change default execution role and select "Use an existing role". In the dialog box that opens up look for **"MasterAutoTaggingLambda"**, this is the role we created in the previous step.
g.- Click "Create function" button
h.- Under Code source > In Environment click `lambda_function.py`
i.- Delete all existing code an replace it with the code provided in the `CreateTagCreatorID.py` file
j.- Once you paste the new code click "Deploy"
j.- In the Code Source menu click Test
k.- In "Configure test event" leave Create new test event selected, In event template leave "Hello-world". In name type "create_tags", leave the rest as it is and click "Create Test" Button. Voila your lambda function is set!

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/6.png)

## 5. Create SNS Topic 
Create a topic - **"SNStoAutoTaggingLambda"** and Subscribe it to Lambda Function **"AutoTagging"** *in ReceiverAccount*. So let us follow the next steps:

a.- Be sure you are in us-east-1 region (SNS works across regions, but still is a regional resource)
b.- At the console screen go to services and type in the text box "sns" or under All ```
```
services > Aplication Intergration > Simple Notification Service
```
c. -CLick at the Simple Notification Service
e.- In the menu to the left click Topics and then The `"Create Topic"` orange buttom.
f.- In Create topic window choose Stardard, In Name type **"SNStoAutoTaggingLambda"**
g.- In the Access policy section we keep the Basic method 
h.- Click Create topic buttom. The topic is created.
i.- Now, we create the subscription. Click the Create subscription button.
j. In Details > Topic ARN look for the topic created in the previous steps
k.-In Protocol choose AWS Lambbda and look for the ARN of the lambda function **AutoTagging.**
l.- Hit the Create Subscription Button. Voila! the subscription is done.

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/7.png)

## 6. In `CloudWatch` in *Receiver Account* add the necessary permissions to `Event Buses` 
In Event Buses we have to manage event bus permissions to enabble passing event metadata:
a.- Be sure you are in us-east-1 region in *Receiver Account*
b.- At the console screen go to services and type in the text box `"Cloudwatch"` or under All
```
services > Management & Governance > Cloudwatch
```
c.- In `Event Buses` item in the menu go to `Event Buses`
d.- Under the permissions section click add permission. A "Add Permission" dialog box opens up. In the Type text box click the arrow and select Organization. In Organization ID select My Organization, your organization Id "my-org-id-1234" should be pre-populated. Hit the Add blue button.

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/9.png)

A Resource-based policy for default event bus is automatically generated.
To check the policy go to ```Amazon EventBridge > Event buses > default``` and you check Permissions tab you will see a Resource-based policy like this
The default event bus name is something like this - `arn:aws:events:us-east-1:111111111111:event-bus/default`

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/8.png)

And the resulting policy would look something like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "this-is-how-i-pass-events-btwn-accounts-in-my-org",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:111111111111:event-bus/default",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalOrgID": "my-organization-id"
      }
    }
  }]
}
```


## 7 In Receiver Account create an EventBridge Rule in us-east-1 -or Virginia Region and use as target SnsSendToLambda.
Create a rule that captures all creation events in `Sender Acccount` using `AWS API Call via CloudTrail` and select **SnsSendToLambda** as target:
a.- Be sure you are in `us-east-1` region in `Receiver Account` 
b.- At the console screen go to services and type in the text box `"EventBridge"` or under
```All services > Application Integration > Amazon EventBridge```
c.- In the Amazon EventBridge menu select Rules and click "Create Rule" button
d.- Under Name and Description > Name type **"EventAutoTaggingRule**"
e.- Add a Description **"Rule to send creation events to SnsSendToLambda"** if you choose to, it is optional
f.- In Define pattern choose ```"Event pattern" > Custom Pattern```
g.- Copy paste the following json in Event Pattern Text Box
```json
{
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventName": [
      {
        "prefix": "Create"
      },
      {
        "prefix": "Put"
      },
      "RunInstances",
      "AllocateAddress"
    ]
  }
}
```
... Click "Save"
Notice that this is exactly the same rule we used in CloudWatch in Receiver Account

h.- In Select event bus leave it as it is, `"AWS default event bus"` and `"Enable the rule on the selected bus"`
i.- In Select` Targets > in Target click the text box, scroll up and select "SNS Topic"`
j.- In Topic text box select **"SnsSendToLambda"**
k.- Click `"Create Rule" `button. 

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/9.png)

## 8  In *Linked Account* create a matching `EventBridge Rule` in same region (we are using us-east-1 - Virginia Region) and use as target the` event Bus `in matching us-east-1 region in *Receiver Account*.
Create a rule that captures all creation events in `Sender Acccount` using `AWS API Call via CloudTrail` and select default event bus as target:
a.- Be sure you are in us-east-1 region in `Sender Account` 
b.- At the console screen go to services and type in the text box `"EventBridge"` or under ``All services > Application Integration > Amazon EventBridge```

c.- In the ```Amazon EventBridge menu select Rules and click "Create Rule" button``
d.- Under Name and ```Description > Name type "EventAutoTaggingRule"``
e.- Add a Description "Rule to send creation events to default event bus in receiver account" if you choose to, it is optional
f.- In Define pattern choose ``"Event pattern" > Custom Pattern``
g.- Copy paste the following json in the Event Pattern Text Box
```json
{
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventName": [
      {
        "prefix": "Create"
      },
      {
        "prefix": "Put"
      },
      "RunInstances",
      "AllocateAddress"
    ]
  }
}
```
...Click "Save"
Notice that this is exactly the same rule we used in CloudWatch in Receiver Account

h.- In Select event bus leave it as it is, ```"AWS default event bus" ```and "Enable the rule on the selected bus"

i.- In ``Select Targets > in Target click the text box, scroll up and select "Event bus in another AWS account"``
j.- In Event Bus text box type `"arn:aws:events:us-east-1:111111111111:event-bus/default"` (be sure to replace the Account number with your designated Receiver Account)
k.- Select "Create a new role for this specific resource". EventBridge will create a role for you with the right permissions to pass events into the event bus. Click configure details button.

l.- Click "Create Rule" button. 

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/10.png)

## 9. Add the necessary permissions to Event Buses in CloudWatch in Linked Account
In `Event Buses` we have to manage event bus permissions to enabble passing event metadata:
a.- Be sure you are in us-east-1 region in *Sender Account*
b.- At the console screen go to services and type in the text box `"Cloudwatch"` or under ```All services > Management & Governance > Cloudwatch```
c.- In `Event Buses` item in the menu go to `Event Buses`.
d.- Under the permissions section click add permission. A `"Add Permission"` dialog box opens up. In the Type text box click the arrow and select Organization. In `Organization ID `select My Organization, your organization Id `"my-org-id-1234"` should be pre-populated. Hit the Add blue button.


A Resource-based policy for default event bus is automatically generated.
To check the policy go to ```Amazon EventBridge > Event buses > default ```and you check Permissions tab you will see a Resource-based policy like this
The default event bus name is something like this - `arn:aws:events:us-east-1:222222222222:event-bus/default`

And the resulting Reso policy would look something like this:
```json
{
  "Version": "2012-10-17",
  "Statement": [{. 
    "Sid": "this-is-how-i-pass-events-btwn-accounts-in-my-org",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:222222222222:event-bus/default",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalOrgID": "my-organization-id"
      }
    }
  }]
}
```

## 10. Deploy a VPC in *Linked Account* and Check the Tags
Either by console or by AWS CLi SDK for boto3 deploy a Vpc or any resource that you desire.
Using the AWS Console:
a. In *Sender Account,* in us-east-1 go to the resource tab
b. In the services search text box type vpc or under "Networking & Content Delivery" look for VPC. Click VPC
c.- In the menu to the left click "Your VPCs"
d.- In Your VPCs window click "Create VPC" button
e.- In Create VPC > VPC settings > Name tag type test-project or any name you want to.
f.- In IPv4 CIDR block type 10.0.0.0/24, leave the rest of the settings as it is.
g.- Click the "Create VPC" button.
{pegar imagen aqui}
h.- You will be redirected to the newly created vpc window details. under the "Tags" tab click it and check for the tags. 

![alt text](https://raw.githubusercontent.com/SynergygraphicIB/Automatization-of-Tag-Creator-based-on-UserName-Across-Accounts/main/img/11.png)

You will see the Following tags; create_at, UserName, Name, and creatorId. 



### Note: To implement the function in different regions, repeat steps 4 to 8 and replace the region values as applicable
