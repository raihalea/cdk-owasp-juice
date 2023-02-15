from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecsp,
    aws_wafv2 as wafv2,
    Stack, CfnOutput
)
from constructs import Construct

class CdkOwaspJuiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(
            self,
            "vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name='public',
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                ec2.SubnetConfiguration(
                    name='private',
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
            ]
        )

        # ECS
        cluster=ecs.Cluster(self, "ecs-cluster",
                              cluster_name="ecs-cluster", vpc=vpc)

        # ECS pattern
        ecsp_service=ecsp.ApplicationLoadBalancedFargateService(
            self,
            "ecs_service",
            cluster=cluster,
            task_image_options=ecsp.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("bkimminich/juice-shop")),
            public_load_balancer=True
        )

        # WAF IPSet
        ipset = wafv2.CfnIPSet(
            self,
            "ipset",
            addresses = ["198.51.100.0/24"],
            ip_address_version="IPV4",
            scope="REGIONAL",
            name="myIP"
        )

        # WAF WebACL
        mywebacl = wafv2.CfnWebACL(
            self,
            id="webacl",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow=wafv2.CfnWebACL.AllowActionProperty(), block=None),
            scope="REGIONAL",

            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="owasp-waf-webacl",
                sampled_requests_enabled=True
            ),
            description="WAF for owasp juice shop",
            name="owasp-waf",
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="IPblock",
                    priority=10,
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="owasp-waf-ipbloack",
                        sampled_requests_enabled=True
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        not_statement=wafv2.CfnWebACL.NotStatementProperty(
                            statement=wafv2.CfnWebACL.StatementProperty(
                                ip_set_reference_statement={
                                    "arn": ipset.attr_arn
                                }
                            )
                        )
                    ),
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        block=wafv2.CfnWebACL.BlockActionProperty(
                            custom_response=wafv2.CfnWebACL.CustomResponseProperty(
                                response_code=403
                            )
                        )
                    )
                )
            ]
        )

        associate_webacl = wafv2.CfnWebACLAssociation(
            self,
            "associate_webacl",
            resource_arn=ecsp_service.load_balancer.load_balancer_arn,
            web_acl_arn=mywebacl.attr_arn
        )

        CfnOutput(
            self,
            "albarn",
            value=ecsp_service.load_balancer.load_balancer_arn
        )
