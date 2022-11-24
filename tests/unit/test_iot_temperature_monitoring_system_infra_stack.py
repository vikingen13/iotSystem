import aws_cdk as core
import aws_cdk.assertions as assertions

from iot_temperature_monitoring_system_infra.iot_temperature_monitoring_system_infra_stack import IotTemperatureMonitoringSystemInfraStack

# example tests. To run these tests, uncomment this file along with the example
# resource in iot_temperature_monitoring_system_infra/iot_temperature_monitoring_system_infra_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IotTemperatureMonitoringSystemInfraStack(app, "iot-temperature-monitoring-system-infra")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
