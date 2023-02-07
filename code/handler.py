import json
import boto3
import cfnresponse
import logging
import os
import sys

# Logging functionality
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    handlers=[stdout_handler],
)
logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO").upper()))

client = boto3.client("ec2")
resource = boto3.resource("ec2")

responseData = {}
physicalResourceId = {}


def handler(event, context):
    """
    If VpcId is provided in ResourceProperties, delete all ingress and egress
    rules for SGs with group-name 'default' in given VPC.

    If ALL = True via ResourceProperties, delete all ingress and egress rules
    for SGs with group-name 'default' in *ALL VPCs*
    """
    logger.info(f"Event: {json.dumps(event)}")
    if context:
        logger.info(f"Context: {context}")

    try:
        req_type = event["RequestType"]
    except:
        req_type = None

    cfn_req_delete(req_type, event, context, responseData, physicalResourceId)

    try:
        VpcId = event["ResourceProperties"]["VpcId"]
    except:
        VpcId = None

    try:
        ALL = event["ResourceProperties"]["ALL"]
    except:
        ALL = None

    if ALL:
        logger.info("ALL: True - Processing all VPCs in current region")
        for VpcId in list_vpcs():
            delete_rules(VpcId)
    elif VpcId:
        logger.info(f"Processing single VPC only")
        delete_rules(VpcId)
    else:
        logger.info(
            'Nothing to do. Provide either "ALL" : True or "VpcId" : "<vpcid>" via event["ResourceProperties"]'
        )

    cfn_req_other(req_type, event, context, responseData, physicalResourceId)


def list_vpcs():
    vpcs = []
    try:
        response = client.describe_vpcs()["Vpcs"]
        for vpc in response:
            vpcs.append(vpc["VpcId"])
    except Exception as e:
        logger.info(f"Error: {e}")
        raise
    return vpcs


def delete_rules(VpcId):
    logger.info(f'Deleting SG rules for all "default" SGs in VPC {VpcId}')
    response = client.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": ["default"]},
            {"Name": "vpc-id", "Values": [VpcId]},
        ]
    )

    for sg in response["SecurityGroups"]:
        sgid = sg["GroupId"]
        sg = resource.SecurityGroup(sgid)

        if sg.ip_permissions:
            logger.info(f"{json.dumps(sg.ip_permissions)}")
            try:
                sg = resource.SecurityGroup(sgid)
            except Exception:
                raise

            try:
                sg.revoke_ingress(IpPermissions=sg.ip_permissions)
                logger.info(f"{sgid}: Ingress rules deleted")
            except Exception:
                logger.info(f"{sgid}: No ingress rules")
                pass  # We don't' care if there are no rules (MissingParameter)

            try:
                sg.revoke_egress(IpPermissions=sg.ip_permissions)
                logger.info(f"{sgid}: Egress rules deleted")
            except Exception:
                logger.info(f"{sgid}: No egress rules")
                pass
        else:
            logger.info(f"{sgid}: No SG rules to delete")


def cfn_req_delete(req_type, event, context, responseData, physicalResourceId):
    if req_type != None:
        if req_type == "Delete":
            try:
                cfn_success(event, context, responseData, physicalResourceId)
                return
            except Exception as e:
                logger.error("Lambda execution has failed! (lambda_handler)", e)
                cfn_failed(event, context, responseData, physicalResourceId)
                return


def cfn_req_other(req_type, event, context, responseData, physicalResourceId):
    if req_type != None:
        try:
            cfn_success(event, context, responseData, physicalResourceId)
            return
        except Exception as e:
            cfn_failed(event, context, responseData, physicalResourceId)
            logger.error("Lambda execution has failed! (lambda_handler)", e)
            return


def cfn_success(event, context, responseData, physicalResourceId):
    cfnresponse.send(
        event, context, cfnresponse.SUCCESS, responseData, physicalResourceId
    )


def cfn_failed(event, context, responseData, physicalResourceId):
    cfnresponse.send(
        event, context, cfnresponse.FAILED, responseData, physicalResourceId
    )


if __name__ == "__main__":
    """
    If this script is executed directly, ...
    """
    event = {
        "ResourceProperties": {
            # "VpcId": "vpc-1234567890abcdefg",
            "ALL": True,
        },
    }
    handler(event, None)
