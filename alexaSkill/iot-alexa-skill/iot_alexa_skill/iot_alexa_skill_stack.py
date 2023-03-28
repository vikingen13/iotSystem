from aws_cdk import (
    Duration,
    Stack,
    CfnParameter
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
from aws_cdk import Stack, aws_s3_deployment as s3deploy, aws_lambda as _lambda, aws_iam as iam

class IotAlexaSkillStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #define parameters
        #alexa skill id
        myAlexaSkillId = CfnParameter(self, "alexaSkillId", type="String",
            description="The ID of the Alexa skill that will invoke the lambda function.")
        
        #timestream db name
        myTimestreamDBName = CfnParameter(self, "timeStreamDBName", type="String",
            description="The name of the timestream db where the data are stored.")

        #web site to host the skill images
        myCloudFrontSite = CloudFrontToS3(self, 'iotAlexaSkill-cloudfront-s3')

        #deploy the images for the skill
        s3deploy.BucketDeployment(self, "DeployWebsite",
           sources=[s3deploy.Source.asset("./webdist")],
            destination_bucket=myCloudFrontSite.s3_bucket,
            destination_key_prefix="web"
        )

        #create the lambda layer including the Alexa Skill Kit SDK
        myLayer = _lambda.LayerVersion(self, "AlexaSkillKitLayer",
            code=_lambda.Code.from_asset("iot_alexa_skill/ask-sdk-layer/ask-sdk.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8,_lambda.Runtime.PYTHON_3_9, _lambda.Runtime.PYTHON_3_7],            
            description="Alexa Skill Kit SDK for Python"
            )
        
        #create the lambda function to handle the skill
        myLambdaFunction = _lambda.Function(self, "AlexaSkillFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("iot_alexa_skill/alexa_lambda_function"),
            handler="lambda_function.lambda_handler",
            layers=[myLayer],
            environment={
                "DATABASE_NAME": myTimestreamDBName.value_as_string,                
                "CLOUD_FRONT_SITE": myCloudFrontSite.cloud_front_web_distribution.distribution_domain_name
            },
            timeout=Duration.seconds(20)
        )

        #Allow the Alexa skill to triggers the function
        myLambdaFunction.add_permission("AlexaSkillFunctionPermission",
            principal=iam.ServicePrincipal("alexa-appkit.amazon.com"),
            event_source_token=myAlexaSkillId.value_as_string,
            action="lambda:InvokeFunction"
        )

        #Add the timestream readonly managed policy to the lambda function
        myLambdaFunction.role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonTimestreamReadOnlyAccess"))

        
