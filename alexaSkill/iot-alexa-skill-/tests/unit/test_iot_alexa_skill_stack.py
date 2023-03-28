import aws_cdk as core
import aws_cdk.assertions as assertions

from iot_alexa_skill.iot_alexa_skill_stack import IotAlexaSkillStack

# example tests. To run these tests, uncomment this file along with the example
# resource in iot_alexa_skill/iot_alexa_skill_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IotAlexaSkillStack(app, "iot-alexa-skill")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
