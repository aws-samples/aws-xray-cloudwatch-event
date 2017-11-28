# Notification & Alarms for AWS X-Ray using Amazon CloudWatch

## License

This sample application is licensed under the Apache 2.0 License.

## Before you begin
1. You will need an active AWS account to proceed. Create one at https://aws.amazon.com/ .
2. Permission to run AWS CloudFormation template that will create Amazon S3 buckets, AWS Lambda functions, Amazon CloudWatch events, CloudWatch rules and AWS IAM Roles. To learn more about CloudFormation, see https://aws.amazon.com/cloudformation/.
3. You will need Python to deploy the CloudFormation template and run the sample app. You can download and install Python from https://www.python.org/.
4. To generate alerts and notifications, you will need an application that is instrumented and sending data to X-Ray. To get started with AWS X-Ray please visit: https://aws.amazon.com/xray/

## Overview
This sample app will help you setup SMS and email alerts when services in your application have elevated latency, or error and fault rates.

![Alt text](/Documentation/architecture.png?raw=true "Sample app architecture and overview")

## Information on pricing
This sample app uses AWS X-Ray, Amazon CloudWatch, AWS Lambda and Amazon SNS. You will be charged based on pricing for each of these individual services. Please refer to the overview section above to understand the architecture of this app and the resources it'll create. The pricing information for the services used in this application is as follows:

AWS X-Ray: https://aws.amazon.com/xray/pricing/
Amazon CloudWatch: https://aws.amazon.com/cloudwatch/pricing/
AWS Lambda: https://aws.amazon.com/lambda/pricing/
Amazon SNS: https://aws.amazon.com/sns/pricing/

## Getting started
### a. Information for notification
The sample app requires the following information to successfully notify you. Please note that your AWS account will be charged by Amazon SNS for these notifications beyond the free tier. For Amazon SNS pricing information please visit: https://aws.amazon.com/sns/pricing/
1. You can configure notifications as follows:
```
{
	"alerts":
	{
		"default":
		{
			"responseunitthreshold":<type: integer. Value representing minutes>,
			"errorpercentagethreshold":<type: float. Value between 0 and 1>,
			"faultpercentagethreshold":<type: float. Value between 0 and 1>,
			"throttlepercentagethreshold":<type: float. Value between 0 and 1>
		}
	},
	"analyzeservicemapminutes":<type: integer. The schedule (in minutes) that determines when CloudWatch Events triggers the Lambda function and time duration for analyzing the X-Ray service map>,
	"evaluationperiodforcwalarm":<type: integer. The evaluation period for your CloudWatch alarm>,
	"communications":
	{
		"sms":
		[
			"type:Phone number (without dashes) with country and area code. Format: 19876543210",
			"type:Phone number (without dashes) with country and area code. Format: 19876543210"
		],
		"email":
		[
			"type: email. Format: abcd@efgh.com",
			"type: email. Format: abcd@efgh.com"
		]
	}

}
```
2. (optional) If you would like to only get notified for specific services in your application, you can add individual service sections:
```
"alerts":
	{
	    <service_name_1>":
		{
			"responseminutesthreshold":<type: integer. Value representing minutes>,
			"errorpercentagethreshold":<type: float. Value between 0 and 1>,
			"faultpercentagethreshold":<type: float. Value between 0 and 1>,
			"throttlepercentagethreshold":<type: float. Value between 0 and 1>,
			"type":<type: string. The type of the node that is shown in your X-Ray service map console>
		},
		<service_name_2>":
		{
			"responseminutesthreshold":<type: integer. Value representing minutes>,
			"errorpercentagethreshold":<type: float. Value between 0 and 1>,
			"faultpercentagethreshold":<type: float. Value between 0 and 1>,
			"throttlepercentagethreshold":<type: float. Value between 0 and 1>,
			"type":<type: string. The type of the node that is shown in your X-Ray service map console>
		}
	}
```

### b. Install the sample app
The CloudFormation template will create the required resources such as S3 buckets, CloudWatch events, CloudWatch rules, IAM roles and Lambda function. Note: You have to update xraycloudwatchevent.json as described above prior to installing the sample app.

1. Git clone this repository.
2. Go to Setup/ directory.
```
cd Setup/
```
3. Run install.py script
```
python install.py
```
4. Provide your sample app name and region when requested by the install.py script.


### c. Uninstall the sample app
Uninstalling the sample app is easy as well. It removes any relevant S3 bucket and resources created by CloudFormation for this app.

1. Go to Setup/ directory.
```
cd Setup/
```
2. Run uninstall.py script
```
python uninstall.py
```
3. Provide your sample app name and region when requested by the uninstall.py script.

## Using the sample app
1. The sample app is an AWS Lambda function, which is triggered by a CloudWatch event at the scheduled time defined by you.
2. This sample app analyzes your AWS X-Ray service graph, aggregated at the provided time window and sends out a CloudWatch event in case the latency, error or fault rates breach the threshold. You can define a custom threshold using the xraycloudwatch.json file.
3. On matching the pattern defined in the CloudWatch Rule, the CloudWatch Event will invoke the SNS topic to send a SMS message to the provided phone number.
4. The CloudWatch Alarm will be trigerred if TriggeredRules > 0 in the evaluation period, which is also defined in the xraycloudwatch.json file, to invoke another SNS topic that sends out an email.
