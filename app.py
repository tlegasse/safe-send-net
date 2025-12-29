#!/usr/bin/env python3
import os

import aws_cdk as cdk

from server.server_stack import ServerStack
from client.client_stack import ClientStack

env_USA = cdk.Environment(account="851725395952", region="us-east-1")

app = cdk.App()
ServerStack(app, "ServerStack", env=env_USA)
ClientStack(app, "ClientStack", env=env_USA)

app.synth()
