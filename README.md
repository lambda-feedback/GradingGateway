# Grading Gateway

## Brief Operation Description

Containerised lambda function which handles all grading requests directly from the Problem Set SPA. Triggered by requests made through the Amazon API Gateway, dispatches requests to the following services:

- If an algorithm pipeline is supplied (list of _algorithm functions_ to apply to a response before grading), will dispatch the grade block to the respective services.
- For non-algorithmic functions, will fetch the answer for a specific response area from the _Problem Sets Database_.
- Ultimately, all grade _blocks_ are graded by a _Grading Lambda Function_, which supply a grade, and potential feedback to be sent back to the SPA.

Furthermore, the idea is that the function catches any data formatting and auth issues as early as possible. ie before sending the block out to each of the resources, which would waste time.

## Input Format

Blocks that are sent to this function need to follow a specific structure in order to be dealt with effectively:

```json
{
  "command": "grade",
  "block": {
    "response": "<response input by user on the web app>",
    "responseID": "<id used to locate the correct answer in Sets DB>",
    "gradingFunction": "<grading function name>",
    "gradingParams": {
      "<optional grading function params>"
    },
    // dict of other responses submitted by the user on the same page, collected before grading
    // pipeline stages use these when modifying the grade block
    "requirements": { 
      "previous_response": "<response object>",
      "..."
    },
    "algorithmPipeline": [
      {
        "algorithmFunction": "<algorithm function name>",
        "params": {
          "<optional function params>"
        }
      },
      "..."
    ]
  }
}
```

## Error output shape

If an error occurs at any point in the grading process, it will be aborted, and the error returned in the form:

```json
{
  "error": {
    "level": "<stage at which the error occurred>",
    "description": "<error description>"
  }
}
```

## Output format

The function will directly output whatever the selected grading function's output was

## Future improvements:

- The grading and algorithm functions are all lambda functions. Instead of issuing requests to them via their API Gateways, we could just invoke them directly (using the boto3.client('lambda') client). This might reduce latency
  - [Calling lambda functions from lambda functions](https://www.sqlshack.com/calling-an-aws-lambda-function-from-another-lambda-function/)
