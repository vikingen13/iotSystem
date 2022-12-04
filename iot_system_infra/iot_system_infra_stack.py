from aws_cdk import (
    # Duration,
    Stack,
    aws_timestream as timestream,
    CfnParameter
)
from constructs import Construct

class IotSystemInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #we create the parameter for the Timstreamdb Name
        myTimeStreamDBName = CfnParameter(self, "timeStreamDBName", type="String",
            description="The name of the time stream DB where the data will be stored.")

        #we create the timestream DB
        cfn_database = timestream.CfnDatabase(self, "MyCfnDatabase",
            database_name=myTimeStreamDBName.value_as_string            
        )
