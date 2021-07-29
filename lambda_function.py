import json
import random
import os
from grade import grade


def handler(event, context):
    """Main lambda function handler
    Calls specific functions based on a 'command' value required in the event body
    """

    # Request data is in the event body as it comes from an AWS API Gateway
    command = event["body"].get("command")

    if command == "grade":
        return grade(event)

    elif command == "random":
        return random_grade()

    else:
        return {
            "error": {
                "statusCode": 400,
                "description": "Command either not given or invalid. (request body needs a 'command' field)",
            }
        }


# For testing purposes, send a random grade
def random_grade():
    rand = random.getrandbits(1)
    return {"grades": [{"isCorrect": bool(rand)}]}
