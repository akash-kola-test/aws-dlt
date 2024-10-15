import os
import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _):
    logger.info("Lambda function invoked with event: %s", event)

    is_running: bool = event.get("isRunning")
    if is_running:
        logger.info("Task is already running. Exiting.")
        return event

    TEST_AWS_REGION = os.environ.get("TEST_AWS_REGION")
    SCENARIOS_BUCKET = os.environ.get("SCENARIOS_BUCKET")

    test_id, prefix = (
        event.get("test_id"),
        event.get("prefix")
    )

    task_count, task_definition, cluster, container_name, subnet = (
        int(event.get("test_task_config").get("task_count")),
        event.get("test_task_config").get("task_definition"),
        event.get("test_task_config").get("cluster"),
        event.get("test_task_config").get("container_name"),
        event.get("test_task_config").get("subnet")
    )

    if container_name is None or len(container_name) == 0:
        raise NameParameterNeededException()

    if subnet is None or len(subnet) == 0:
        raise SubnetIDNeededException()

    logger.info(
        "Running tasks with the following parameters: "
        "Region: %s, Task Count: %d, Test ID: %s, Cluster: %s, "
        "Task Definition: %s, Prefix: %s, S3 Bucket: %s",
        TEST_AWS_REGION,
        task_count,
        test_id,
        cluster,
        task_definition,
        prefix,
        SCENARIOS_BUCKET,
    )

    ecs = boto3.client("ecs", region_name=TEST_AWS_REGION)

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                "environment": [
                    {"name": "S3_BUCKET", "value": SCENARIOS_BUCKET},
                    {"name": "TEST_ID", "value": test_id},
                    {"name": "PREFIX", "value": prefix},
                    {"name": "AWS_REGION", "value": TEST_AWS_REGION},
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
                "subnets": [ subnet ],
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
    event["isRunning"] = is_running

    return event


class NameParameterNeededException(Exception):
    def __init__(self, msg: str = "Name parameter is needed for container overrides") -> None:
        super().__init__(msg)
        self.msg = msg


class SubnetIDNeededException(Exception):
    def __init__(self, msg: str = "Subnet IDs parameter is needed for aws vpc network configuration") -> None:
        super().__init__(msg)
        self.msg = msg
