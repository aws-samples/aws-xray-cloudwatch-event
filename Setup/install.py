'''
/*Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at http://aws.amazon.com/apache2.0/ or in the "license" file accompanying this file.
This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.*/
'''

import os
import json

appname = raw_input("Enter a unique name for your app {pattern:^[a-z0-9]+$}:")

print("Your appname:"+appname+" will be used for naming your CloudFormation stack, public s3 bucket and as a prefix as a prefix to identify all the Lambda functions and IAM Roles associated with your app")

print("The region should be the same as your service running in X-Ray. If your service runs in multiple regions then you should have multiple instances of this sample app running in each region.")

sampleappregion = raw_input("Enter the aws region where you would like this sample app to be deployed. (Default: us-west-2): ") or "us-west-2"

# Setting time to analyze servicemap. Default set to 6 hours if not found in xraycloudwatcheventfile.json.
xraycloudwatcheventfile = open('xraycloudwatchevent.json', 'r').read()
xraycloudwatcheventdict = json.loads(xraycloudwatcheventfile)

analyzeservicemapminutes = xraycloudwatcheventdict['analyzeservicemapminutes'] if 'analyzeservicemapminutes' in xraycloudwatcheventdict else 360
evaluationperiodforcwalarm = xraycloudwatcheventdict['evaluationperiodforcwalarm'] if 'evaluationperiodforcwalarm' in xraycloudwatcheventdict else 1

print("Setting to analyze your service map every: %d minutes" % analyzeservicemapminutes)

# Zip the Lambda function and node folders
print("Zipping the file that has to be uploaded to AWS Lambda")
zipcommand = "zip -q -r Archive.zip xraycloudwatchevent.py"
os.system(zipcommand)

# Create s3 bucket to store the Archive
print("Creating S3 bucket that will have the Archive.zip file for AWS Lambda")
s3createcommand = "aws s3api create-bucket --create-bucket-configuration LocationConstraint=%s --acl private --bucket lambdacodexcw" % sampleappregion
os.system(s3createcommand)

# Upload Archive.zip to s3 bucket
print("Uploading Archive.zip to the S3 bucket")
s3uploadcommand = "aws s3 cp Archive.zip s3://lambdacodexcw"
os.system(s3uploadcommand)

# Deploy resources in a CloudFormation stack
periodcwalarm=analyzeservicemapminutes*60 # Converting analyzeservicemapminutes from minutes to seconds
print("Deploying resources from the Cloudformation template")
cfcommand = "aws --region %s cloudformation deploy --template-file xraycloudwatchevent.template --stack-name %s --parameter-overrides appname=%s analyzeservicemapminutes=%d periodcwalarm=%d evaluationperiodforcwalarm=%d --capabilities CAPABILITY_NAMED_IAM" % (sampleappregion, appname, appname, analyzeservicemapminutes,periodcwalarm,evaluationperiodforcwalarm)
print(cfcommand)
os.system(cfcommand)

print("Completed deploying resources from the Cloudformation template.")

# Upload xraycloudwatchevent.json to s3 bucket
print("Uploading xraycloudwatchevent.json to the S3 bucket")
s3uploadcommand = "aws s3 cp xraycloudwatchevent.json s3://"+appname+"-xraycloudwatcheventbucket"
os.system(s3uploadcommand)

# Delete bucket that has the lambda code
deletes3lambdabucket = "aws s3 rb s3://lambdacodexcw --force"
os.system(deletes3lambdabucket)

print("Deleted temporary s3 bucket")
