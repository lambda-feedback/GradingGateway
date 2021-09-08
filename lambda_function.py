import json
import random
import os
from grade import grade


def handler(event, context):
    """Main lambda function handler
    Calls specific functions based on a 'command' value required in the event body
    """

    # Request data is in the event body as it comes from an AWS API Gateway
    if not event.get("body", None):
        return {
            "error": {
                "statusCode": 400,
                "description": "Body not found. (request event needs a 'body' field)",
            }
        }

    # Parse body
    if type(event["body"]) != dict:
        try:
            event["body"] = json.loads(event["body"])
        # Catch Decode errors and return the problems back to the requester.
        except json.JSONDecodeError as e:
            return {
                "error": {
                    "type": "JSONDecodeError",
                    "description": "Couldn't decode data from `body`",
                }
            }

    command = event["body"].get("command")

    if command == "grade":
        return grade(event)

    elif command == "random":
        return random_grade()

    else:
        return {
            "error": {
                "statusCode": 400,
                "description": f"Command [{command}] either not given or invalid. (request body needs a 'command' field)",
            }
        }


# For testing purposes, send a random grade
def random_grade():
    rand = random.getrandbits(1)
    return {"grades": [{"isCorrect": bool(rand)}]}
