'''
Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at http://aws.amazon.com/apache2.0/ or in the "license" file accompanying this file.
This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
'''

import os
import boto3
import datetime
import json
from botocore.exceptions import ClientError
from collections import defaultdict

# The APP_NAME is retrieved from Lambda's environment variable
APP_NAME = os.environ['APP_NAME']

# The region should be the same as your service running in X-Ray.
# If your service runs in multiple regions then you should have multiple instances of this app running
REGION_NAME = os.environ['AWS_REGION']

# Message types
LOG_MESSAGE = "logmessages"
ERROR_MESSAGE = "errormessages"

# Change this value based on your preference for verbosity of logs
VERBOSE_TIER = True

# Alert types for CloudWatch event
RESPONSE_ALERTS = 'Response'
ERROR_ALERTS = 'Error'
THROTTLE_ALERTS = 'Throttle'
FAULT_ALERTS = 'Fault'

# Default minutes for every scan of X-Ray-GetServiceGraph API
service_graph_minutes = 10

# SNS Topic for the CloudWatch Event. This SNS topic will be used by CloudWatch Event to send the appropriate notification.
CW_EVENT_SNS = os.environ['CW_EVENT_SNS']

# SNS Topic for the CloudWatch Alarm. This SNS topic will be used by CloudWatch Alarm to send the appropriate notification when the alarm goes to an ALARM state.
CW_ALARM_SNS = os.environ['CW_ALARM_SNS']

xrayclient = boto3.client(
	'xray',
	region_name=REGION_NAME
)

snsclient = boto3.client(
	'sns',
	region_name=REGION_NAME
)

s3resource = boto3.resource(
	's3',
	region_name=REGION_NAME
)

cweventsclient = boto3.client('events')

cwclient = boto3.client('cloudwatch')

def print_message(printString, status=LOG_MESSAGE):
	# Print log messages only when verbose is selected
	if status == LOG_MESSAGE and VERBOSE_TIER is True:
		print(printString)

	# Print all error messages
	if status == ERROR_MESSAGE:
		print(printString)


def get_trace_ids_from_trace_summary(tracesummary_dict):
	trace_ids = list()

	if type(tracesummary_dict) != dict:
		print_message("Trace Summary is expected to be a dict", ERROR_MESSAGE)
		return trace_ids

	if type(tracesummary_dict) == dict:
		if 'TraceSummaries' in tracesummary_dict:
			print_message("Found TraceSummaries key in tracesummary_dict")
			for valueOuter in tracesummary_dict['TraceSummaries']:
				if type(valueOuter) == dict:
					print_message("valueOuter is a dict")
					trace_ids.append(valueOuter['Id'])

	return trace_ids


def handle_datetime(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def put_metric_in_cloudwatch():
	try:
		cwclient.put_metric_data(
			Namespace = 'XCW/'+ APP_NAME,
			MetricData = [
		        {
		            'MetricName': APP_NAME + 'xraycloudwatchmetric',
		            'Timestamp': datetime.datetime.utcnow(),
		            'Value': 1,
		            'Unit': 'Count'
		        },
		    ]
		)
	except ClientError as ceputmetricdata:
		print_message("Error while calling put_metric_data: %s" % ceputmetricdata, ERROR_MESSAGE)
		raise



def put_event_in_cloudwatch(source, detail_type, detail, purpose=None, topic_arn=False):
	# put_event for response time
	print_message("Putting %s event for %s" % (source, purpose))
	try:
		response_for_put_event = cweventsclient.put_events(
			Entries=[
				{
					'Time': datetime.datetime.utcnow(),
					'Source': source,
					'DetailType': detail_type,
					'Detail': detail
				}
			]
		)
		print_message(json.dumps(response_for_put_event, default=handle_datetime, indent=4, sort_keys=True))
	except ClientError as ceputevent:
		print_message("Error while calling put_event for %s : %s" % (purpose, ceputevent), ERROR_MESSAGE)
		raise


def subscribe_to_sms(communications_dict):
	topic_name = CW_EVENT_SNS
	topic_arn = False
	existing_subscription_endpoints = []

	try:
		topic = snsclient.create_topic(Name=topic_name) # Returns back the topic_arn if topic is already present
		topic_arn = topic['TopicArn']
		print_message("TopicArn: %s" % topic_arn)

		# Get all existing endpoints for subscriptions
		try:
			response_for_listof_subscriptions = snsclient.list_subscriptions_by_topic(
				TopicArn=topic_arn
			)
			#browse through each subscription endpoint
			for each_sub in response_for_listof_subscriptions['Subscriptions']:
				existing_subscription_endpoints.append(each_sub['Endpoint'])
		except ClientError as celistsubs:
			print_message("Error while calling list_subscriptions_by_topic: %s" % celistsubs, ERROR_MESSAGE)
			raise

		if type(communications_dict) != dict:
			print_message("Expected communications_dict to be a dictionary. Cannot subscribe to SMS or Email otherwise.",ERROR_MESSAGE)
			return False

		if 'sms' in communications_dict:
			for sms_number in communications_dict['sms']:
				if(sms_number in existing_subscription_endpoints):
					print_message("Number already subscribed")
				else:
					print_message("Number to subscribe for SMS: %s" % sms_number)
					snsclient.subscribe(
						TopicArn=topic_arn,
						Protocol='sms',
						Endpoint=sms_number
					)
	except ClientError as cesnscreatetopic:
		print_message("Error while calling create_topic for %s: %s" % (topic_name, cesnscreatetopic), ERROR_MESSAGE)
		raise

	return topic_arn


def subscribe_to_email(communications_dict):
	topic_name = CW_ALARM_SNS
	topic_arn = False
	existing_subscription_endpoints = []

	try:
		topic = snsclient.create_topic(Name=topic_name) # Returns back the topic_arn if topic is already present
		topic_arn = topic['TopicArn']
		print_message("TopicArn: %s" % topic_arn)

		# Get all existing endpoints for subscriptions
		try:
			response_for_listof_subscriptions = snsclient.list_subscriptions_by_topic(
				TopicArn=topic_arn
			)
			#browse through each subscription endpoint
			for each_sub in response_for_listof_subscriptions['Subscriptions']:
				existing_subscription_endpoints.append(each_sub['Endpoint'])
		except ClientError as celistsubs:
			print_message("Error while calling list_subscriptions_by_topic: %s" % celistsubs, ERROR_MESSAGE)
			raise

		if type(communications_dict) != dict:
			print_message("Expected communications_dict to be a dictionary. Cannot subscribe to SMS or Email otherwise.",ERROR_MESSAGE)
			return False

		if 'email' in communications_dict:
			for email_address in communications_dict['email']:
				if(email_address in existing_subscription_endpoints):
					print_message("Email address already subscribed")
				else:
					print_message("Email address: %s to subscribe for sending emails" % email_address)
					snsclient.subscribe(
						TopicArn=topic_arn,
						Protocol='email',
						Endpoint=email_address
					)
	except ClientError as cesnscreatetopic:
		print_message("Error while calling create_topic for %s: %s" % (topic_name, cesnscreatetopic), ERROR_MESSAGE)
		raise

	return topic_arn


def check_set_rule_put_event_in_cloudwatch(alert_type_string, service_name_string, xraycloudwatcheventdict, subscribe=True, put_event=True):
	topic_arn = False # This will contain the topicArn on successful registration of SMS
	rule_name = APP_NAME + '-xcw.alerts'

	communications_dict = xraycloudwatcheventdict['communications'] if 'communications' in xraycloudwatcheventdict else dict()

	if put_event != True:
		print_message("Skipping checking for rule and putting event for %s" % alert_type_string)
		return

	# Subscribe to SMS
	if subscribe == True:
		topic_arn = subscribe_to_sms(communications_dict)

	# Emails are subscribed for CloudWatch Alarm
	topic_arn_for_email = subscribe_to_email(communications_dict)

	# put_event in CloudWatch
	print_message("Putting CloudWatch Event for %s for %s" % (alert_type_string, service_name_string))

	now = datetime.datetime.now()

	source_string = "%s" % (rule_name)
	detail_type_string = "XCW Notification for Alerts"
	detail_string = '{"status":"%s %s at %s."}' % (alert_type_string, service_name_string, now.strftime("%Y-%m-%d %H:%M"))

	put_event_in_cloudwatch(source_string,
		detail_type_string,
		detail_string,
		alert_type_string,
		topic_arn
	)

	put_metric_in_cloudwatch()

def put_aggregated_breaches(aggregate_alert_dict,xraycloudwatcheventdict):
	lenagg = len(aggregate_alert_dict.keys())

	for alert_type_key, list_value in aggregate_alert_dict.items():
		lenlist = len(list_value)
		if (lenlist > 0):
			service_name_string = "%s" % list_value[0] if lenlist == 1 else "%s+%d nodes" % (list_value[0],lenlist-1)

	if(lenagg > 0):
		first_alert_string = "%s" % list(aggregate_alert_dict.keys())[0] if lenagg == 1 else "%s and other thresholds have been breached for" % list(aggregate_alert_dict.keys())[0]
		check_set_rule_put_event_in_cloudwatch(first_alert_string,service_name_string,xraycloudwatcheventdict)

	return

def get_service_graph_and_analyze(xraycloudwatcheventdict):
	if type(xraycloudwatcheventdict) == dict:
		if 'analyzeservicemapminutes' in xraycloudwatcheventdict:
			service_graph_minutes = xraycloudwatcheventdict['analyzeservicemapminutes']
			print_message("analyzeservicemapminutes found in xraycloudwatcheventfile: %d" % service_graph_minutes)

	print_message("Calling get_service_graph")

	try:
		service_graph_response = xrayclient.get_service_graph(
		StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=service_graph_minutes),
		EndTime=datetime.datetime.utcnow(),
		)
		print_message("Response from get_service_graph")
		print_message(json.dumps(service_graph_response, default=handle_datetime, indent=4, sort_keys=True))
	except ClientError as ceservice:
		print_message("Cannot continue. Error while getting service_graph_response: %s" % ceservice)
		raise

	if 'Services' not in service_graph_response:
		print_message("No 'Services' found in your X-Ray get_service_graph API call",ERROR_MESSAGE)
		return

	# Dict that aggregates different alerts
	aggregate_alert_dict = defaultdict(list)

	for value_services in service_graph_response['Services']:
		service_name = value_services['Name']
		node_type = value_services['Type']

		# Go through summarystatistics
		total_count = value_services['SummaryStatistics']['TotalCount'] if 'SummaryStatistics' in value_services else 0
		error_count = value_services['SummaryStatistics']['ErrorStatistics']['TotalCount'] if 'SummaryStatistics' in value_services else 0
		throttle_count = value_services['SummaryStatistics']['ErrorStatistics']['ThrottleCount'] if 'SummaryStatistics' in value_services else 0
		fault_count = value_services['SummaryStatistics']['FaultStatistics']['TotalCount'] if 'SummaryStatistics' in value_services else 0
		total_response_time = value_services['SummaryStatistics']['TotalResponseTime'] if 'SummaryStatistics' in value_services else 0

		print_message("SummaryStatistics for %s of type %s: TotalCount: %d; ErrorCount: %d; ThrottleCount: %d; faultCount:%d; TotalResponseTime:%d" % (service_name,node_type, total_count, error_count, throttle_count, fault_count, total_response_time))

		# Check if the service_name is present in the xraycloudwatchevent.json file or if user wants alerts for all nodes in servicemap
		if (service_name in xraycloudwatcheventdict['alerts'] and node_type in xraycloudwatcheventdict['alerts'][service_name]['type'] and total_count > 0) or ('default' in xraycloudwatcheventdict['alerts'] and total_count > 0): #check if the service name is found in your xraycloudwatch json file
			avg_response_time = total_response_time/total_count
			error_percent = (error_count/total_count) * 100
			throttle_percent = (throttle_count/total_count) * 100
			fault_percent = (fault_count/total_count) * 100

			#set key_service_name to default if service_name not found in xraycloudwatcheventdict
			key_service_name = service_name if service_name in xraycloudwatcheventdict['alerts'] else 'default'

			print_message("Looking at user defined responseTime for %s and found %s : %d" % (service_name,key_service_name, xraycloudwatcheventdict['alerts'][key_service_name]['responseunitthreshold']))
			if avg_response_time >= xraycloudwatcheventdict['alerts'][key_service_name]['responseunitthreshold']:
				aggregate_alert_dict[RESPONSE_ALERTS].append(service_name)
			else:
				print_message("ResponseTime is: %d for %s . Not setting up CloudWatch events for %s" % (avg_response_time, key_service_name, service_name))

			print_message("Looking at user defined errorPercent for %s and found %d" % (service_name, xraycloudwatcheventdict['alerts'][key_service_name]['errorpercentagethreshold']))
			if error_percent >= xraycloudwatcheventdict['alerts'][key_service_name]['errorpercentagethreshold']:
				aggregate_alert_dict[ERROR_ALERTS].append(service_name)
			else:
				print_message("ErrorPercent is: %d for %s . Not setting up CloudWatch events for %s" % (error_percent, key_service_name, service_name))

			print_message("Looking at user defined throttlePercent for %s and found %d" % (service_name, xraycloudwatcheventdict['alerts'][key_service_name]['throttlepercentagethreshold']))
			if throttle_percent >= xraycloudwatcheventdict['alerts'][key_service_name]['throttlepercentagethreshold']:
				aggregate_alert_dict[THROTTLE_ALERTS].append(service_name)
			else:
				print_message("ThrottlePercent is: %d for %s . Not setting up CloudWatch events for %s" % (throttle_percent, key_service_name, service_name))

			print_message("Looking at user defined faultPercent for %s and found %d" % (service_name, xraycloudwatcheventdict['alerts'][key_service_name]['faultpercentagethreshold']))
			if fault_percent >= xraycloudwatcheventdict['alerts'][key_service_name]['faultpercentagethreshold']:
				aggregate_alert_dict[FAULT_ALERTS].append(service_name)
			else:
				print_message("FaultPercent is: %d for %s . Not setting up CloudWatch events for %s" % (fault_percent, key_service_name, service_name))

	put_aggregated_breaches(aggregate_alert_dict,xraycloudwatcheventdict)


def main():
	print_message("Getting json from S3")
	try:
		s3resource.Bucket(APP_NAME + '-xraycloudwatcheventbucket').download_file('xraycloudwatchevent.json', '/tmp/xraycloudwatchevent.json')
		print_message("Downloading file to xraycloudwatchevent.json file")
		xraycloudwatcheventfile = open('/tmp/xraycloudwatchevent.json').read()
	except ClientError as ces:
		print_message("Error while getting xraycloudwatchevent.json: %s" % ces)
		raise

	print_message("xraycloudwatchevent.json file:")
	print_message(xraycloudwatcheventfile)

	xraycloudwatcheventdict = json.loads(xraycloudwatcheventfile)

	get_service_graph_and_analyze(xraycloudwatcheventdict)


def handler(event, context):
	main()
