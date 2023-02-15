import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_owasp_juice.cdk_owasp_juice_stack import CdkOwaspJuiceStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_owasp_juice/cdk_owasp_juice_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkOwaspJuiceStack(app, "cdk-owasp-juice")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
