import os
from aws_cdk import (
    aws_lambda,
    aws_dynamodb,
    aws_lambda_python_alpha,
    Stack,
    RemovalPolicy,
    CfnOutput,
)

from constructs import Construct

class ServerStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        stack_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(stack_dir)

        secrets_table = aws_dynamodb.Table(
            self, "secrets_table",
            partition_key=aws_dynamodb.Attribute(
                name="id",
                type=aws_dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="expiresAt",  # Auto-delete
            removal_policy=RemovalPolicy.DESTROY
        )

        get_secrets_lambda = aws_lambda_python_alpha.PythonFunction(
            self,
            "secret_get_secrets_lambda_function",
            reserved_concurrent_executions=10,
            log_retention=None,
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            entry=os.path.join(project_root, "static", "secret-get"),
            index="main.py",
            handler="lambda_handler",
        )

        get_secrets_lambda.add_environment("TABLE_NAME", secrets_table.table_name)

        secrets_table.grant_write_data(get_secrets_lambda)
        secrets_table.grant_read_data(get_secrets_lambda)

        create_secrets_lambda = aws_lambda_python_alpha.PythonFunction(
            self,
            "create_secrets_lambda_function",
            reserved_concurrent_executions=10,
            log_retention=None,
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            entry=os.path.join(project_root, "static", "secret-create"),
            index="main.py",
            handler="lambda_handler",
        )

        secrets_table.grant_write_data(create_secrets_lambda)

        create_secrets_lambda.add_environment("TABLE_NAME", secrets_table.table_name)


        put_url = create_secrets_lambda.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE,
            cors=aws_lambda.FunctionUrlCorsOptions(
                # allowed_origins=["https://safe-send.net"],
                allowed_origins=["*"],
                allowed_methods=[aws_lambda.HttpMethod.PUT]
            )
        )

        get_url = get_secrets_lambda.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE,
            cors=aws_lambda.FunctionUrlCorsOptions(
                allowed_origins=["https://safe-send.net"],
                # allowed_origins=["*"],
                allowed_methods=[aws_lambda.HttpMethod.GET]
            )
        )

        CfnOutput(self, "PutSecretUrl", 
                value=put_url.url,
                description="API endpoint to create secrets"
                )

        CfnOutput(self, "GetSecretUrl",
                value=get_url.url, 
                description="API endpoint to retrieve secrets"
                )
