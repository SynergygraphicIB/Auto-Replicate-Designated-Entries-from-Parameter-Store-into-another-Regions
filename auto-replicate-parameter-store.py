#!/usr/bin/env python3

# SPDX-License-Identifier: MIT-0

# Identity-based AWS resource tagger run by AWS Lambda

# Import AWS modules for python
import botocore
import boto3
# Import JSON
import json
# Import RegEx module
import re
import os




def lambda_handler(event, context):
    
    
    def extract_replicate_parameter_store(client, id ):
        try:
            response = client.list_tags_for_resource(
                ResourceType='Parameter',
                ResourceId=id
            )
            response= response ["TagList"]
            for tags in response:
                if (tags["Key"] == "replicate") and (tags["Value"] == "yes") :
                    return True
                elif (tags["Key"] == "replicate"):
                    return(tags["Value"])
            return False
        except botocore.exceptions.ClientError as error:
            print("Boto3 API returned error: ", error)
            
            
    def validate_region(region):
        try:
            ec2 = boto3.client('ec2')
            regions= ec2.describe_regions()
            region_names = [x["RegionName"] for x in regions["Regions"]]
            if(region in region_names):
                return True
            print("Region no valid")
            return False
            
        except botocore.exceptions.ClientError as error:
            print("Boto3 API returned error: ", error)
    
    if("Scheduled" in event["detail-type"]):
        try:
            ssm_client = boto3.client('ssm')
            parameters=ssm_client.describe_parameters()
            
            for parameter in parameters["Parameters"]:
                if(extract_replicate_parameter_store(ssm_client,parameter["Name"])):
                    
                                        
                    regions= os.environ['region']
                    regions= regions.strip(" ")
                    regions= regions.split(",")
                    
                    response = ssm_client.get_parameter(Name= parameter["Name"],WithDecryption=True)
                    response = response["Parameter"]
                    
                    for region in regions:
                        
                        if(validate_region(region)):
                            ssm_client_replicate =boto3.client('ssm', region_name = region )
                            
                            if  parameter.get("Description") == None:
                                parameter["Description"] = "   "
                            
                            respuesta = ssm_client_replicate.put_parameter(
                                Name = parameter.get("Name"),
                                Description =parameter.get("Description"),
                                Value = response.get("Value"),
                                Type = response.get("Type"),
                                Overwrite = True,
                                Tier = parameter.get("Tier"),
                                DataType = parameter.get("DataType")
                            )


        except botocore.exceptions.ClientError as error:
            print("Boto3 API returned error: ", error)
    elif (event["detail"]["eventName"]== "PutParameter"):
        event=event["detail"]
        
        try:
            regions= os.environ['region']
            regions= regions.strip(" ")
            regions= regions.split(",")
            
            
            for region in regions:
                
                if(validate_region(region)):
                    ssm_client_replicate =boto3.client('ssm', region_name = region )
                
                    requestParameters = event["requestParameters"] 
                    if  requestParameters.get("description") == None:
                       requestParameters["description"] = "   "
                    response = ssm_client_replicate.put_parameter(
                        Name = requestParameters.get("name"),
                        Description =requestParameters.get("description"),
                        Value = requestParameters.get("value"),
                        Type = requestParameters.get("type"),
                        Overwrite = True,
                        Tier = requestParameters.get("tier"),
                        DataType = requestParameters.get("dataType")
                    )
        except botocore.exceptions.ClientError as error:
            print("Boto3 API returned error: ", error)

