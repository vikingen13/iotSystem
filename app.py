#!/usr/bin/env python3
import os

import aws_cdk as cdk

from iot_system_infra.iot_system_infra_stack import IotSystemInfraStack
from esp8266tempsensors.esp8266tempsensors import esp8266tempsensors


app = cdk.App()
myInfraStack = IotSystemInfraStack(app, "IotSystemInfraStack")

esp8266tempsensors(app,"esp8266tempsensors",env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
