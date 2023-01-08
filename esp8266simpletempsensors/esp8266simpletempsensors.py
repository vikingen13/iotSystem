from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_iot as iot,
    aws_timestream as timestream,
    CfnParameter,
    aws_iotevents as iotevents,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    # aws_sqs as sqs,
)
from constructs import Construct
from esp8266simpletempsensors import esp8266simpletempsensors_monitoring_detectormodel


class esp8266simpletempsensors(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        #we create the parameter for the Timstreamdb Name
        myTimeStreamDBName = CfnParameter(self, "timeStreamDBName", type="String",
            description="The name of the time stream DB where the data will be stored.")

        ####################################################################################
        # IoT Events

        # IoT Events: Execution role
        iot_events_execution_role = iam.Role(self, "IoTEventsExecutionRole", assumed_by=iam.ServicePrincipal("iotevents.amazonaws.com"))
        iot_events_execution_role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["SNS:Publish"]
        ))

        # IoT Events: Input
        inputDefinitionProperty = iotevents.CfnInput.InputDefinitionProperty(
            attributes=[{"jsonPath": "devicename"}]
        )

        iot_events_input = iotevents.CfnInput(self, "esp8266simpletempsensorsConnectivityStatusInput",
                                              input_definition=inputDefinitionProperty,
                                              input_name="esp8266simpletempsensorsConnectivityStatusInput",
                                              input_description="Input for connectivity status updates for esp8266simpletempsensors"

                                              )
        # IoT Events: Detector Model
        detector_model_definition = iotevents.CfnDetectorModel.DetectorModelDefinitionProperty(
            initial_state_name=esp8266simpletempsensors_monitoring_detectormodel.initial_state_name,
            states=esp8266simpletempsensors_monitoring_detectormodel.get_states(self))

        iot_events_model = iotevents.CfnDetectorModel(self, "esp8266simpletempsensorsConnectivityModel",
                                                      detector_model_definition=detector_model_definition,
                                                      detector_model_name="esp8266simpletempsensorsConnectivityModel",
                                                      detector_model_description="Detector model for esp8266simpletempsensors connectivity status",
                                                      key="devicename",
                                                      evaluation_method="BATCH",
                                                      role_arn=iot_events_execution_role.role_arn)


        ####################################################################################
        # SNS topic
        sns_topic = sns.Topic(self, "esp8266simpletempsensorsNotificationTopic",
                              display_name="Topic to use for notifications about esp8266simpletempsensors events like connect or disconnect",
                              topic_name="esp8266simpletempsensorsNotificationTopic"
                              )

        email_address = CfnParameter(self, "emailforalarms")
        sns_topic.add_subscription(subscriptions.EmailSubscription(email_address.value_as_string))


        #create the iot policy for the esp8266 sensors
        myPolicy = iot.CfnPolicy(self, "esp8266simpletempsensors-policy",
            policy_name="esp8266simpletempsensors-policy",
            policy_document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                    actions=["iot:Publish"],
                    resources=["arn:aws:iot:{}:{}:topic/esp8266simpletempsensors/*".format(self.region,self.account)]
                ),
                iam.PolicyStatement(
                    actions=["iot:Connect"],
                    resources=["arn:aws:iot:{}:{}:client/*".format(self.region,self.account)]
                )
            ])
        )

        #create the table in an existing DB
        myTimeStreamTable = timestream.CfnTable(self, "esp8266simpletempsensorsTimestreamTable",
            database_name=myTimeStreamDBName.value_as_string,
            magnetic_store_write_properties={"EnableMagneticStoreWrites":False},
            retention_properties={ "MemoryStoreRetentionPeriodInHours": "24", "MagneticStoreRetentionPeriodInDays": "365" },
            table_name="esp8266simpletempsensors"
        )

        #create the roles to allow the iot rule to write in the timestream db and to write in the error log
        myTimeStreamWriteRole = iam.Role(self, "TimeStreamWriteRole",
            role_name="esp8266simpletempsensorsTimeStreamWriteRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role to allow the esp8266simpletempsensorsTopicRule iot rule to write in timestream DB",
            inline_policies={
                'AllowWrite': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=['timestream:WriteRecords'],
                            resources=[myTimeStreamTable.attr_arn]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=['timestream:DescribeEndpoints'],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        myCloudWatchLogGroupName = "esp8266simpletempsensorsIotRuleError"
        #create the roles to allow the iot rule to write in the cloudwatch loggroup in case of error
        myCloudwatchWriteRole = iam.Role(self, "CloudwatchWriteRole",
            role_name="esp8266simpletempsensorsCloudwatchWriteRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role to allow the esp8266simpletempsensorsTopicRule iot rule to write in cloudwatch logs",
            inline_policies={
                'AllowWrite': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["logs:CreateLogStream","logs:DescribeLogStreams","logs:PutLogEvents"],
                            resources=["arn:aws:logs:{}:{}:log-group:{}:*".format(self.region,self.account,myCloudWatchLogGroupName)]
                        )
                    ]
                )
            }
        )


        #create the iotrule to write in the db
        myTopicRule = iot.CfnTopicRule(self, "esp8266simpletempsensorsTopicRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                actions=[iot.CfnTopicRule.ActionProperty(
                    timestream=iot.CfnTopicRule.TimestreamActionProperty(
                        database_name=myTimeStreamDBName.value_as_string,
                        dimensions=[iot.CfnTopicRule.TimestreamDimensionProperty(
                            name="device",
                            value="${topic(2)}"
                        )],
                        role_arn=myTimeStreamWriteRole.role_arn,
                        table_name=myTimeStreamTable.attr_name,
                    )
                )],
                error_action=iot.CfnTopicRule.ActionProperty(
                    cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                        log_group_name=myCloudWatchLogGroupName,
                        role_arn=myCloudwatchWriteRole.role_arn
                    )
                ),
                sql="SELECT temperature FROM 'esp8266simpletempsensors/#'",

                rule_disabled=False
            ),
                        
            # the properties below are optional
            rule_name="esp8266simpletempsensorsTopicRule",
        )


        #create the roles to allow the monitoring iot rule to send an iot Event and to write in the error log
        myIoTEventsPublishRole = iam.Role(self, "IoTEventsPublishRole",
            role_name="esp8266simpletempsensorsIoTEventsPublishRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role to allow the esp8266simpletempsensorsMonitoringTopicRule iot rule to send an IotEvents",
            inline_policies={
                'BatchPutMessage': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=['iotevents:BatchPutMessage'],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        #create the iotrule to publish in IotEvents
        myMonitoringTopicRule = iot.CfnTopicRule(self, "esp8266simpletempsensorsMonitoringTopicRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                actions=[iot.CfnTopicRule.ActionProperty(
                    iot_events=iot.CfnTopicRule.IotEventsActionProperty(
                        input_name=iot_events_input.input_name,
                        batch_mode=False,
                        role_arn=myIoTEventsPublishRole.role_arn                        
                    )
                )],
                error_action=iot.CfnTopicRule.ActionProperty(
                    cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                        log_group_name=myCloudWatchLogGroupName,
                        role_arn=myCloudwatchWriteRole.role_arn
                    )
                ),
                sql="SELECT topic(2) as devicename FROM 'esp8266simpletempsensors/#'",

                rule_disabled=False
            ),
                        
            # the properties below are optional
            rule_name="esp8266simpletempsensorsMonitoringTopicRule",
        )

