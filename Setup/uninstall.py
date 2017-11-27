import os

appname = raw_input("Enter your sample app's name that you chose while installing the sample app {pattern:^[a-z0-9]+$}: ")
sampleappregion = raw_input("Enter the aws region where had deployed this sample app. (Default: us-west-2): ") or "us-west-2"

# Empty the app's s3 buckets first
deleteappbucket = "aws s3 rm s3://%s-xraycloudwatcheventbucket --recursive --only-show-errors" % appname
print("Deleting your app's s3 bucket contents using commands: %s" % deleteappbucket)
os.system(deleteappbucket)

# Deleting the s3 bucket
deleteimages = "aws s3 rm s3://%s-xraycloudwatcheventbucket --recursive --only-show-errors" % appname
print(deleteimages)
os.system(deleteimages)
print("Deleted the app's s3 bucket")

# Delete cloudformation stack
deletecloudformationstack = "aws --region %s cloudformation delete-stack --stack-name %s" % (sampleappregion, appname)
print("Deleting your sample app's CloudFormation stack using command: %s" % deletecloudformationstack)
os.system(deletecloudformationstack)
print("Deleted CloudFormation stack for the app. Please check https://console.aws.amazon.com/cloudformation for any details.")
