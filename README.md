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

### 1. Log in into you account and get the AWS/SSM Managed Key ID 
Log in to Account ID 111111111111. This is the account number we are going to use as reference in this exercise. When rewriting policies or Rules remember to replace 111111111111 with your account number.

a.- At the console screen go to services and type in the text box `"KMS"` or under All
    ```Services > Security, Identity, & Compliance > Key Management Service (KMS)```
b.- In `Key Management Service` (KMS) menu > go to `AWS managed keys` and click `"aws/ssm"` Under AWS managed keys list
c.- In General Configuration copy and save the Key ARN. For the purposes of this example the Key ID is "arn:aws:kms:us-east-1:111111111111:key/75fcc799-de1b-42c7-9a12-a23b31111111111"

![alt text](imagen de KMS con vainas difuminadas que no se vean)

### 2. Setting up the Lamdba Role **auto-replicate-parameter-store-role**
1. We create an **policy.json** to allow auto-replicate-parameter-store-role to have all required autorizations to replicate Parameter Store Entries:

    a.- At the console screen go to services and type in the text box `"IAM"` or under All
        ```Services > Security, Identity, & Compliance > IAM```
    b.- In `Identity and Access Managment (IAM) menu > go to Policies` and click `"Create policy"` button
    c.- Click Create policy next.
    d.- In Create policy window select JSON tab. Click and copy-paste the following policy and click the "Next: tags" button:

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
                    "arn:aws:kms:*:111111111111:key/75fcc799-de1b-42c7-9a12-a23b31111111111",
                    "arn:aws:ssm:*:111111111111:parameter/*"
                ]
            }
        ]
    }
    ```

    e.- Click "Next: Review" button
    f.- In Review policy window in Name type **"policy.json"**
    g.- In Description type "Rule to enable **auto-replicate-parameter-store-role** Rule to replicate parameter store entries" and click "Create policy". 

**Note** Under Resource...

```json
            "Resource": [
                "arn:aws:kms:*:111111111111:key/75fcc799-de1b-42c7-9a12-a23b31111111111",
                "arn:aws:ssm:*:111111111111:parameter/*"
            ]
```
                
 ... replace the KMS Key arn and the Account number wherever applicable
        
![alt text](imagen)

2.- Create "auto-replicate-parameter-store-role"

    a.- Be sure you are in `Account 111111111111`
    b.- At the console screen go to services and type in the text box `"IAM"` or under All services > Security, Identity, & Compliance > IAM
    d.- In Create Role window > Under "Select type of trusted entity" keep AWS service as your choice
    e.- In "Choose a use case" select "Lambda" and click "Next: Permissions" button
    f.- In next window, under Attach Permissions policies click Filter policies and checkmark "Customer managed"
    j.- Scroll down and checkmark the Customer managed policy **"policy.json"**
    k.-  Click "Next:Tags" button and click "Next: Review" button too
    l.- Under Review, in Role name `*` type **"auto-replicate-parameter-store-role"** 
    m.- In Role description type "Resource Role to replicate parameter store entries" 
        Observe that in Trusted entities you got AWS service: lambda.amazonaws.com and the recently created policy attached to the role
    n.- Click "Create Role Button"

    ![alt text](Imagen de Role auto-replicate-parameter-store-role siendo creado)


### 3. Deploy auto-replicate-parameter-store Lambda Function in us-east-1

We deploy our lambda function in Virginia Region/us-east-1. This is the endpoint for any new entry in the parameter store in us-east-1 that is to be replicated to any other region that is configured in the pipeline.

Create a **auto-replicate-parameter-store** lambda function with the console:

    a.- First, be sure you are in us-east-1  (It seems repetive, but it is easy to be in the wrong region and fail to do the pipeline configuration) . In the console click the services tab and look for Lamdba under
    ```
    All services > Compute > Lambda or just type lambda in the text box. then hit Lambda
    ```
    b.- In the AWS lambda window go to Functions.
    c.- Click the "Create function" buttom.
    d.- You will the following options to create your function Author from scratch, Use blueprint, Container Image, and Browse serverless app repository, choose Author from scratch.
    e.- In Function name type **"auto-replicate-parameter-store"** or any name you choose to, in Runtime look for Python 3.9
    f.- In Permissions - click Change default execution role and select "Use an existing role". In the dialog box that opens up look for **"auto-replicate-parameter-store-role"**, this is the role we created in the previous step.
    g.- Click "Create function" button
    h.- Under Code source > In Environment click `lambda_function.py`
    i.- Delete all existing code an replace it with the code provided in the `auto-replicate-parameter-store.py` file
    j.- Once you paste the new code click "Deploy"
    k.- Click the `Configuration` tab an go to `Environment variables`. 
    l.- In `Environment variables` click `Edit` Button and a new `Edit environment variables` window will open.
    m.- Click `Add environment variable` Next under `Key` type region, and under `Value` type us-west-2,us-east-2 (Notice that when adding different regions we use comma to separate the values and no spaces). Click `Save`

![alt text](imagen de creacion de la variables de entorno)

Voila your lambda function is set!

![alt text](imagen de creacion de lambda)


### 4. In EventBridge in us-east-1 create a rule and use  as target to replicate entries at moment of creation.
Create a rule that captures all the parameter store entry creation events in `us-east-1` using `AWS API Call via CloudTrail` and select **auto-replicate-parameter-store** as target in order to automatically replicate the entry at the moment of deployment to whatever regions were set in the `Environment variables` at the lambda function:

    a.- Be sure you are in `us-east-1` region 
    b.- At the console screen go to services and type in the text box `"EventBridge"` or under
    ```All services > Application Integration > Amazon EventBridge```
    c.- In the Amazon EventBridge menu select Rules and click "Create Rule" button
    d.- Under Name and Description > Name type **"EventPutParameter**"
    e.- Add a Description **"Rule to send parameter store entry creation events to auto-replicate-parameter-store lambda function"** if you choose to, it is optional
    f.- In Define pattern choose ```"Event pattern" > Custom Pattern```
    g.- Copy paste the following json in Event Pattern Text Box
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
    ... Click "Save"

    Notice that "PutParameter" is the Event Name that is generated when a new entry is created at the parameter store

    h.- In `Select event bus` section leave it as it is ```Select an event bus`>`AWS default event bus``` 
    i.- In Select` Targets > in Target click the text box, scroll up and select "Lambda Function"`
    j.- In Topic text box select **"auto-replicate-parameter-store"**
    k.- Click `"Create Rule" `button. 

    ![alt text](imagen de creacion de regla desde eventBridge)


### 5. Configure a Schedule Rule that updates Parameter Store Entries set to be replicated across regions based on a fixed rate

Create a Schedule Rule to trigger  **auto-replicate-parameter-store** as target:
a.- Be sure you are in `us-east-1` region 
b.- At the console screen go to services and type in the text box `"EventBridge"` or under
```All services > Application Integration > Amazon EventBridge```
c.- In the Amazon EventBridge menu select Rules and click "Create Rule" button
d.- Under Name and Description > Name type **"replicate-parameters-by-schedule**"
e.- Add a Description **"Rule to trigger the replication of Paramater Store Entries set to replicate/yes across regions"** if you choose to, it is optional
f.- In Define pattern choose ```" > Schedule"```
g.- In `Fixed rate every` Type `24` and select `Hours` (Or just choose any time schedule you want)
h.- In `Select event bus` section leave it as it is ```Select an event bus`>`AWS default event bus``` 
i.- In Select` Targets > in Target click the text box, scroll up and select "Lambda Function"`
j.- In Topic text box select **"auto-replicate-parameter-store"**
k.- Click `"Create Rule" `button. 

![alt text](imagen de creacion de regla SCHEDULE desde eventBridge)

Note: The Fixed Rate you set determines how many times the parameter store will be updated per day

### 6  Create a new Entry at the Parameter Store with Tags: replicate/yes 
Let us create a new entry at the Parameter Store set to be replicated:

a.- Be sure you are in `us-east-1` region 
b.- At the console screen go to services and type in the text box `"Parameter Store"` or under
```All services > Management & Governance > Systems Manager```    
c.- In the `AWS Systems Manager` menu select `Parameter Store` and click `Create Parameter` button
d.- In ```Create parameter > Parameter details > Name ``` type `test-parameter`
e.- In ```Create parameter > Parameter details > Description — Optional ``` type `Parameter to be replicated in Ohio and Oregon`
f.- In ```Create parameter > Parameter details > Tier ``` leave `Standard`
g.- In ```Create parameter > Parameter details > Type ``` choose `SecureString` (in order to test encryption/decryption capabilities)
h.- In ```Create parameter > Parameter details > KMS key source ``` leave `My current account`
j.- In ```Create parameter > Parameter details > KMS Key ID ``` leave `alias/aws/ssm` 
k.- In ```Create parameter > Parameter details > Value ``` type `Hey it is replicated!`
l.- In ```Tags ``` click `Add tag` 
m.- In ```Key``` text box type `replicate`, and in ```Value``` text box type `yes` and click ```Create parameter```

![alt text](imagen de entry en el parameter store en virginia....)

n.- Now, You will see the same entry replicated at the Paramter Store in us-east-2 and us-west-2

![alt text](imagen de entry en el parameter store en ohio....)



### Note: To implement the replication in other regions, repeat modify the ```Environment Variable > region``` of the lambda function as applicable in your project
