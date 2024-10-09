import boto3
import logging
from typing import List

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

    logger.info("Retrieving task ARNs for cluster: %s", cluster)
    tasksArns = get_tasks_arns(ecs, cluster)
    
    if not tasksArns:
        logger.info("No tasks found for cluster: %s", cluster)
        event["isRunning"] = is_running
        return event

    logger.info("Found task ARNs: %s", tasksArns)
    tasks_result = ecs.describe_tasks(cluster=cluster, tasks=tasksArns)
    tasks = tasks_result.get("tasks", []) or []
    
    logger.info("Described tasks: %s", tasks)
    test_tasks = filter(lambda task: task["group"] == test_id, tasks)

    if any(test_tasks):
        is_running = True
        logger.info("Test tasks are running for test_id: %s", test_id)
    else:
        logger.info("No running tasks found for test_id: %s", test_id)

    event["isRunning"] = is_running
    logger.info("Returning event: %s", event)
    return event


def get_tasks_arns(ecs, cluster_name: str) -> List[str]:
    logger.info("Listing tasks for cluster: %s", cluster_name)
    tasks_result = ecs.list_tasks(cluster=cluster_name)
    tasksArns = tasks_result.get("taskArns", [])
    logger.info("Task ARNs retrieved: %s", tasksArns)
    return tasksArns
