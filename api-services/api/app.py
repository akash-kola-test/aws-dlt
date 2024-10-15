import os
import json
import re
from datetime import datetime, timezone

import boto3


def lambda_handler(event, _):
    if event["resource"] == "/test":
        handle_tests(event)

    return {
        "statusCode": 200,
        "body": {
            "message": "hello world",
        },
    }


def handle_tests(event):
    if event["httpMethod"] == "POST":
        test_id = event["test_id"]

        AWS_TESTS_REGION = os.environ.get("AWS_TESTS_REGION", "us-east-1")
        if AWS_TESTS_REGION != "us-east-1":
            raise InvalidRegionException(AWS_TESTS_REGION)

        ddb = boto3.client("dynamodb", region_name=AWS_TESTS_REGION)
        test_task_config = event["test_task_config"]
        merge_region_infra_config_details(ddb, AWS_TESTS_REGION, test_task_config)

        test_scenario = event["test_scenario"]

        test_name = event["test_name"]
        user_defined_variables = event.get("variables", {})
        test_scenario["scenarios"][test_name]["variables"] = user_defined_variables

        test_scenario["reporting"] = [
            {
                "module": "final-stats",
                "summary": True,
                "percentiles": True,
                "summary-labels": True,
                "test-duration": True,
                "dump-xml": "/tmp/artifacts/results.xml",
            },
        ]

        s3_client = boto3.client("s3", region_name=AWS_TESTS_REGION)
        write_scenario_to_s3(
            s3_client,
            test_scenario,
            test_task_config,
            test_id
        )

        hold_for = test_scenario["execution"][0]["hold-for"]
        test_duration = get_test_duration_seconds(hold_for)

        sfn = boto3.client("stepfunctions", region_name=AWS_TESTS_REGION)
        step_function_params = {
            "test_task_config": test_task_config,
            "test_id": test_id,
            "duration": test_duration,
        }

        start_state_machine_execution(sfn, step_function_params)

        test_description = event["test_description"]
        upload_test_entry_to_db(ddb, test_id, test_description, test_scenario, test_task_config)


def upload_test_entry_to_db(dynamodb, test_id, test_description, test_scenario, test_task_config):
    TESTS_TABLE = os.environ.get("TESTS_TABLE")
    if TESTS_TABLE is None:
        raise TableNotFoundInEnvironmentException()
    dynamodb.put_item(TableName=TESTS_TABLE, Item={
        "test_id": {
            "S": test_id
        },
        "task_count": {
            "N": test_task_config["task_count"]
        },
        "concurrency": {
            "N": test_task_config["concurrency"]
        },
        "test_name": {
            "S": test_scenario["execution"][0]["scenario"]
        },
        "test_description": {
            "S": test_description
        },
        "hold-for": {
            "S": test_scenario["execution"][0]["hold-for"]
        },
        "ramp-up": {
            "S": test_scenario["execution"][0]["ramp-up"]
        },
        "running": {
            "BOOL": True
        }
    })


def start_state_machine_execution(sfn, step_function_params):
    prefix = "".join(reversed(datetime.now(timezone.utc).isoformat().replace("Z", "")))
    TAURUS_STATE_MACHINE_ARN = os.environ.get("TAURUS_STATE_MACHINE_ARN")
    sfn.start_execution(
        stateMachineArn=TAURUS_STATE_MACHINE_ARN,
        input=json.dumps({**step_function_params, "prefix": prefix}),
    )


def get_test_duration_seconds(test_duration):
    split_duration_regex = r"[a-z]+|\d+"
    matches = re.findall(split_duration_regex, test_duration)

    if len(matches) != 2:
        raise InvalidParameterException(
            "Invalid hold-for format. It should contain both a value and a unit."
        )

    duration_value, duration_unit = matches
    duration_value = int(duration_value)

    if duration_unit == "s":
        return duration_value
    elif duration_unit == "m":
        return duration_value * 60
    else:
        raise InvalidParameterException(
            "Invalid hold-for unit, it should be either 'm' or 's'."
        )


def write_scenario_to_s3(s3, test_scenario, test_task_config, test_id):
    test_scenario["execution"][0]["task_count"] = int(test_task_config["task_count"])
    test_scenario["execution"][0]["concurrency"] = int(test_task_config["concurrency"])

    TEST_SCENARIOS_BUCKET = os.environ.get("TEST_SCENARIOS_BUCKET")
    AWS_TESTS_REGION = os.environ.get("AWS_TESTS_REGION", "us-east-1")
    
    s3.put_object(
        Body=json.dumps(test_scenario).encode(),
        Bucket=TEST_SCENARIOS_BUCKET,
        Key=f"test-scenarios/{test_id}-{AWS_TESTS_REGION}.json",
    )


def merge_region_infra_config_details(dynamodb, region: str, test_task_config):
    REGION_INFRA_TABLE = os.environ.get("REGION_INFRA_TABLE")
    response = dynamodb.get_item(
        TableName=REGION_INFRA_TABLE, Key={"region": {"S": region}}
    )

    item = response["Item"]

    test_task_config["subnet"] = item["subnet"]["S"]
    test_task_config["cluster"] = item["cluster"]["S"]
    test_task_config["task_definition"] = item["task_definition"]["S"]
    test_task_config["container_name"] = item["task_container"]["S"]


class InvalidRegionException(Exception):
    def __init__(self, region, message="Invalid region provided"):
        self.region = region
        self.message = f"{message}: {region}"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InvalidParameterException(Exception):
    def __init__(self, message):
        super().__init__(message)


class TableNotFoundInEnvironmentException(Exception):
    def __init__(self, message="not able to find TESTS_TABLE key in environment variables"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
