# Delete all ingress and egress rules from 'default' SG for given VPC or all VPCs

To process single VPC, pass `VpcId` via `event["ResourceProperties"`] via cloudformation custom resource or directly, e.g.

```python
if __name__ == "__main__":
    """
    If this script is executed directly, ...
    """
    event = {
        "ResourceProperties": {
            "VpcId": "vpc-1234567890abcdefg",
            # "ALL": True,
        },
    }
    handler(event, None)
```

To process ALL VPC's in the current region, pass `"ALL": True` directly, e.g.:

```python
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
```

