import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _):
    logger.info("Lambda function invoked with event: %s", event)

    is_running: bool = event.get("is_running")
    if is_running:
        logger.info("Task is already running. Exiting.")
        return event

    region, task_count, test_id, cluster, task_definition, prefix, s3_bucket, container_name, subnets = (
        event.get("region"),
        int(event.get("task_count")),
        event.get("test_id"),
        event.get("cluster"),
        event.get("task_definition"),
        event.get("prefix"),
        event.get("s3_bucket"),
        event.get("container_name"),
        event.get("subnets")
    )

    if container_name is None or len(container_name) == 0:
        raise NameParameterNeededException()

    if subnets is None or len(subnets) == 0:
        raise SubnetIDsNeededException()

    logger.info(
        "Running tasks with the following parameters: "
        "Region: %s, Task Count: %d, Test ID: %s, Cluster: %s, "
        "Task Definition: %s, Prefix: %s, S3 Bucket: %s",
        region,
        task_count,
        test_id,
        cluster,
        task_definition,
        prefix,
        s3_bucket,
    )

    ecs = boto3.client("ecs", region_name=region)

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                "environment": [
                    {"name": "S3_BUCKET", "value": s3_bucket},
                    {"name": "TEST_ID", "value": test_id},
                    {"name": "PREFIX", "value": prefix},
                    {"name": "AWS_REGION", "value": region},
                ],
            },
        ]
    }

    task_params = {
        "group": test_id,
        "launchType": 'FARGATE',
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "assignPublicIp": "ENABLED"
            }
        },
    }

    logger.info("Starting ECS tasks with parameters: %s", task_params)

    try:
        response = ecs.run_task(**task_params)
        logger.info("ECS run_task response: %s", response)
    except Exception as e:
        logger.error("Failed to run ECS task: %s", e)
        raise

    is_running = True
    event["is_running"] = is_running

    return event


class NameParameterNeededException(Exception):
    def __init__(self, msg: str = "Name parameter is needed for container overrides") -> None:
        super().__init__(msg)
        self.msg = msg


class SubnetIDsNeededException(Exception):
    def __init__(self, msg: str = "Subnet IDs parameter is needed for aws vpc network configuration") -> None:
        super().__init__(msg)
        self.msg = msg
