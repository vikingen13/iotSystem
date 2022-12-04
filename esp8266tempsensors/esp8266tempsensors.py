from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_iot as iot,
    aws_timestream as timestream,
    CfnParameter,
    # aws_sqs as sqs,
)
from constructs import Construct


class esp8266tempsensors(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        #we create the parameter for the Timstreamdb Name
        myTimeStreamDBName = CfnParameter(self, "timeStreamDBName", type="String",
            description="The name of the time stream DB where the data will be stored.")


        #create the iot policy for the esp8266 sensors
        myPolicy = iot.CfnPolicy(self, "esp8266tempsensors-policy",
            policy_name="esp8266tempsensors-policy",
            policy_document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                    actions=["iot:Publish"],
                    resources=["arn:aws:iot:{}:{}:topic/esp8266tempsensors/*".format(self.region,self.account)]
                ),
                iam.PolicyStatement(
                    actions=["iot:Connect"],
                    resources=["arn:aws:iot:{}:{}:client/*".format(self.region,self.account)]
                )
            ])
        )

        #create the table in an existing DB
        myTimeStreamTable = timestream.CfnTable(self, "esp8266tempsensorsTimestreamTable",
            database_name=myTimeStreamDBName.value_as_string,
            magnetic_store_write_properties={"EnableMagneticStoreWrites":False},
            retention_properties={ "MemoryStoreRetentionPeriodInHours": "24", "MagneticStoreRetentionPeriodInDays": "365" },
            table_name="esp8266tempsensors"
        )

        #create the roles to allow the iot rule to write in the timestream db and to write in the error log
        myTimeStreamWriteRole = iam.Role(self, "TimeStreamWriteRole",
            role_name="esp8266tempsensorsTimeStreamWriteRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role to allow the esp8266tempsensorsTopicRule iot rule to write in timestream DB",
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

        myCloudWatchLogGroupName = "esp8266tempsensorsIotRuleError"
        #create the roles to allow the iot rule to write in the cloudwatch loggroup in case of error
        myCloudwatchWriteRole = iam.Role(self, "CloudwatchWriteRole",
            role_name="esp8266tempsensorsCloudwatchWriteRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role to allow the esp8266tempsensorsTopicRule iot rule to write in cloudwatch logs",
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
        myTopicRule = iot.CfnTopicRule(self, "esp8266tempsensorsTopicRule",
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
                sql="SELECT temperature FROM 'esp8266tempsensors/#'",

                rule_disabled=False
            ),
                        
            # the properties below are optional
            rule_name="esp8266tempsensorsTopicRule",
        )
