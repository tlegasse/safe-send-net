import os
from aws_cdk import (
    Aws,
    Stack,
    RemovalPolicy,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    CfnOutput,
    aws_route53_targets as route53_targets,
)
from constructs import Construct


# [WARNING] aws-cdk-lib.aws_cloudfront_origins.S3Origin is deprecated.
#   Use `S3BucketOrigin` or `S3StaticWebsiteOrigin` instead.

class ClientStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        client_zone = route53.PublicHostedZone(self, "HostedZone",
                                 zone_name="safe-send.net"
                                 )

        client_site_bucket = s3.Bucket(
            self,
            "client_bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        stack_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(stack_dir)

        deployment = s3deploy.BucketDeployment(
            self,
            "client_bucket_deployment",
            sources=[
                s3deploy.Source.asset(
                    os.path.join(project_root, "static", "client")
                )
            ],
            destination_bucket=client_site_bucket
        )

        origin_access_identity = cloudfront.OriginAccessIdentity(
            self,
            'origin_access_identity',
            comment=f"OAI for the static site from stack:{Aws.STACK_NAME}"
        )

        # Origin with OAI
        origin = origins.S3Origin(
            client_site_bucket,
            origin_access_identity=origin_access_identity
        )

        # Certificate (must be in us-east-1)
        cert = acm.Certificate(self, "SiteCert",
            domain_name="safe-send.net",
            validation=acm.CertificateValidation.from_dns(client_zone)
        )

        # Distribution
        distribution = cloudfront.Distribution(
            self,
            'distribution',
            default_root_object='index.html',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origin,
                compress=True,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            domain_names=["safe-send.net"],
            certificate=cert,
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            enable_logging=False  # Privacy
        )

        # Route53 record
        route53.ARecord(self, "SiteAliasRecord",
            zone=client_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution) # type: ignore
            )
        )

        client_site_output = CfnOutput(
            self,
            "CloudfrontUrl",
            value=f"{distribution.distribution_domain_name}",
            description="The domain name of the static site"
        )
