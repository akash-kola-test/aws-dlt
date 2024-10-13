import boto3
import logging
from typing import Any, Dict, Optional

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _):
    logger.info("Received event: %s", event)

    test_id = event.get("test_id")
    region = event.get("region")
    cluster = event.get("cluster")
    is_running = False

    ecs = boto3.client("ecs", region_name=region)

    nextToken = None

    while True:
        logger.info("Retrieving task ARNs for cluster: %s", cluster)
        tasks = list_tasks(ecs, cluster, nextToken)
        tasks_arns = tasks.get("taskArns", [])
        logger.info("Found task ARNs: %s", tasks_arns)

        if len(tasks_arns) != 0:
            tasks_result = ecs.describe_tasks(cluster=cluster, tasks=tasks_arns)
            described_tasks = tasks_result.get("tasks", []) or []
            logger.info("Described tasks: %s", tasks)

            test_tasks = filter(lambda task: task["group"] == test_id, described_tasks)

            if any(test_tasks):
                is_running = True
                logger.info("Test tasks are running for test_id: %s", test_id)

        nextToken = tasks["nextToken"]
        logger.info("Next token for listing tasks: %s", nextToken)

        if not nextToken:
            break

    event["isRunning"] = is_running
    logger.info("Returning event: %s", event)
    return event


def list_tasks(
    ecs, cluster_name: str, next_token: Optional[str] = None
) -> Dict[str, Any]:
    logger.info("Listing tasks for cluster: %s", cluster_name)
    params = {"cluster": cluster_name}

    if next_token:
        params["nextToken"] = next_token

    tasks_result = ecs.list_tasks(**params)
    tasks_arns = tasks_result.get("taskArns", [])
    next_token = tasks_result.get("nextToken")
    logger.info("Task ARNs retrieved: %s", tasks_arns)

    return {"taskArns": tasks_arns, "nextToken": next_token}
