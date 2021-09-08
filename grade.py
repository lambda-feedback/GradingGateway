import requests as rq
import os
import json


def safe_get(level, url, json=None, headers=None, **kwargs):
    """Utility function wraps a normal requests.get call with proper error handeling
    If the request goes wrong, will return an object containing error details.
    Accepts kwargs that are passed directly to the requests.get call
    """

    # Make the request
    try:
        response = rq.get(url, json=json, headers=headers, **kwargs)
        response.raise_for_status()
    except rq.exceptions.HTTPError as errh:
        return {
            "error": {
                "level": level + " get",
                "description": "A Http Error occurred: " + repr(errh),
                "req_json": json
                if os.getenv("ENV_MODE") == "dev"
                else "ENV_MODE != dev",
            }
        }
    except rq.exceptions.ConnectionError as errc:
        return {
            "error": {
                "level": level + " get",
                "description": "An Error Connecting to the API occurred: " + repr(errc),
                "req_json": json
                if os.getenv("ENV_MODE") == "dev"
                else "ENV_MODE != dev",
            }
        }
    except rq.exceptions.Timeout as errt:
        return {
            "error": {
                "level": level + " get",
                "description": "A Timeout Error occurred: " + repr(errt),
                "req_json": json
                if os.getenv("ENV_MODE") == "dev"
                else "ENV_MODE != dev",
            }
        }
    except rq.exceptions.RequestException as err:
        return {
            "error": {
                "level": level + " get",
                "description": "An Unknown Error occurred: " + repr(err),
                "req_json": json
                if os.getenv("ENV_MODE") == "dev"
                else "ENV_MODE != dev",
            }
        }

    # Get the data
    try:
        data = response.json()
    except json.decoder.JSONDecodeError as errj:
        return {
            "error": {
                "level": level,
                "description": "An Error occured when parsing JSON from response"
                + repr(errj),
            }
        }

    return data


def grade(event):
    """Main function which handles all grading requests directly from the Problem Set SPA.
    Triggered by requests made through the Amazon API Gateway, dispatches requests to:
        - Problem Sets Database
        - Grading Function
        - Algorithmic Function(s)
    """

    # Block to be graded
    block = event["body"].get("block", None)

    if not block:
        return {
            "error": {
                "level": "Gateway",
                "description": "Grading gateway needs a block to grade",
            }
        }

    # First, run the grading block through an Algorithmic function pipeline (if it exists)
    if "algorithmPipeline" in block:
        block = apply_algorithm_pipeline(block)

        # Elevate any errors encountered in the pipeline back to the client
        if "error" in block:
            return block

    # If the block still doesn't have an `answer` field, fetch it from the sets DB
    # algorithm functions might have provided it already (for dynamic questions)
    if "answer" not in block:
        # Send original event headers too, as we need the Auth Token
        answer = get_correct_answer(block, event["headers"])

        # Elevate any errors encountered back to the client
        # (Most likely a permission error hopefully)
        if "error" in answer:
            return answer

        block["answer"] = answer

    # Finally, we can grade the block!
    grade = get_grade(block)

    # Return any errors
    if "error" in grade:
        grade["error"]["level"] = f"Grading Function: {block.get('gradeFunction')}"

    return grade


def apply_algorithm_pipeline(block):
    """Send the supplied block through its algorithm function pipeline
    returns a response block, ready to be sent a grading function"""

    # Iterate through each stage of the algorithm pipeline
    for stage in block["algorithmPipeline"]:
        payload = {
            "command": "execute",
            "block": block,
            "params": stage.get("params", None),
        }

        # Endpoint for the specified algorithm function
        url = os.getenv("ALGORITHM_FUNCTION_BASE_URL") + stage["algorithmFunction"]

        # Carry out the request, handeling the appropriate errors correctly
        level = f"Grading Gateway: Algorithm Function: {stage['algorithmFunction']}"  # for errors

        res = safe_get(
            level, url, json=payload, headers={"Content-Type": "application/json"}
        )

        # If an error occured at a pipeline stage, abort and send it back
        if "error" in res:
            return res
        elif "block" not in res:
            return {
                "error": {
                    "level": level,
                    "description": "Algorithm function did not return block",
                    "raw_response": res
                    if os.getenv("ENV_MODE") == "dev"
                    else "ENV_MODE != dev",
                }
            }

        # Block was mutated by the algorithm function, let's reflect that change
        block = res["block"]

    return block


def get_correct_answer(block, headers):
    """Will fetch the correct answer for a response area specified by response_id
    Request is made to the Problem Sets database, therefore requires an auth token
    """

    level = "Grading Gateway: Get Correct Answer"

    # First, make sure the authorization header was supplied correctly
    auth = headers.get("Authorization", None)
    if not auth:
        return {
            "error": {
                "level": level,
                "description": "The Authorization header was not supplied",
            }
        }

    parts = auth.split()
    if parts[0].lower() != "bearer":
        return {
            "error": {
                "level": level,
                "description": "Authorization header must start with Bearer",
            }
        }
    elif len(parts) == 1:
        raise {
            "error": {
                "level": level,
                "description": "Token not found in Authorization header",
            }
        }
    elif len(parts) > 2:
        return {
            "error": {
                "level": level,
                "description": "Authorization header must be: Bearer token",
            }
        }

    response_id = block.get("response_id", None)

    if not response_id:
        return {
            "error": {
                "level": level,
                "description": "Block needs a `response_id` when answer isn't supplied by algorithm functions or init block",
            }
        }

    # We can now fetch the answer from the sets DB
    payload = {"responseID": response_id}

    answer = safe_get(
        level,
        os.getenv("SETS_DB_API_ANSWER_ENDPOINT"),
        json={"response_id": response_id},
        headers={"Authorization": auth},
    )

    return answer


def get_grade(block):
    """Send the supplied block to its appropriate grading function
    returns a grade/feedback block, ready to be sent to the SPA"""

    # The gradeFunction needs to be specified
    if not block.get("gradeFunction"):
        return {
            "error": {
                "level": "Grading Gateway: Get Grade",
                "description": "`gradeFunction` is a required field, it was either lost in the pipeline or never supplied",
            }
        }

    # Endpoint for the specified grading function
    url = os.getenv("GRADING_FUNCTION_BASE_URL") + block["gradeFunction"]

    # Craft the payload to the grading function
    payload = {
        "response": block.get("response"),
        "answer": block.get("answer"),
        "params": block.get("gradeParams", None),
    }

    # Carry out the request, handeling the appropriate errors correctly
    level = f"Grading Gateway: Grading Function: {block['gradeFunction']}"  # for errors
    grade = safe_get(
        level,
        url,
        json=payload,
        headers={"Content-Type": "application/json", "command": "grade"},
    )

    return grade
