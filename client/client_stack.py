import os
from aws_cdk import (
    Aws,
    Stack,
    Duration,
    RemovalPolicy,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_wafv2 as wafv2,
    CfnOutput,
    aws_route53_targets as route53_targets,
)
from constructs import Construct


# [WARNING] aws-cdk-lib.aws_cloudfront_origins.S3Origin is deprecated.
#   Use `S3BucketOrigin` or `S3StaticWebsiteOrigin` instead.

class ClientStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        waf = wafv2.CfnWebACL(
            self, "WebACL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="CLOUDFRONT",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="safe-send-waf",
                sampled_requests_enabled=True
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimit1000",
                    priority=1,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=1000,
                            aggregate_key_type="IP"
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimit1000",
                        sampled_requests_enabled=True
                    )
                )
            ]
        )

        client_zone = route53.PublicHostedZone(self, "HostedZone",
                                 zone_name="safe-send.net"
                                 )

        client_site_bucket = s3.Bucket(
            self,
            "client_bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        stack_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(stack_dir)


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
            subject_alternative_names=["www.safe-send.net"],
            validation=acm.CertificateValidation.from_dns(client_zone)
        )

        response_headers_policy=cloudfront.ResponseHeadersPolicy(
            self, "SecurityHeaders",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(override=True),
                frame_options=cloudfront.ResponseHeadersFrameOptions(frame_option=cloudfront.HeadersFrameOption.DENY, override=True),
                content_security_policy=cloudfront.ResponseHeadersContentSecurityPolicy(
                    content_security_policy=(
                        "default-src 'self'; "
                        "connect-src 'self' https://*.lambda-url.us-east-1.on.aws; "
                        "script-src 'self'; "
                        "style-src 'self' 'unsafe-inline'"
                    ),
                    override=True
                ),
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.days(730),
                    include_subdomains=True,
                    override=True
                )
            )
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
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                response_headers_policy=response_headers_policy
            ),
            domain_names=["safe-send.net", "www.safe-send.net"],
            certificate=cert,
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            enable_logging=False,
            web_acl_id=waf.attr_arn,
        )

        deployment = s3deploy.BucketDeployment(
            self,
            "client_bucket_deployment",
            sources=[
                s3deploy.Source.asset(
                    os.path.join(project_root, "static", "client")
                )
            ],
            destination_bucket=client_site_bucket,
            distribution=distribution,
            distribution_paths=["/*"]
        )

        # Route53 record
        route53.ARecord(self, "SiteAliasRecord",
            zone=client_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution) # type: ignore
            )
        )

        route53.CnameRecord(self, "WwwAliasRecord",
            zone=client_zone,
            record_name="www",
            domain_name=distribution.distribution_domain_name
        )

        client_site_output = CfnOutput(
            self,
            "CloudfrontUrl",
            value=f"{distribution.distribution_domain_name}",
            description="The domain name of the static site"
        )
