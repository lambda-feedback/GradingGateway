# Grading Gateway

## Brief Operation Description

Containerised lambda function which handles all grading requests directly from the Problem Set SPA. Triggered by requests made through the Amazon API Gateway, dispatches requests to the following services:

- If an algorithm pipeline is supplied (list of _algorithm functions_ to apply to a response before grading), will dispatch the grade block to the respective services.
- For non-algorithmic functions, will fetch the answer for a specific response area from the _Problem Sets Database_.
- Ultimately, all grade _blocks_ are graded by a _Grading Lambda Function_, which supply a grade, and potential feedback to be sent back to the SPA.

Furthermore, the idea is that the function catches any data formatting and auth issues as early as possible. ie before sending the block out to each of the resources, which would waste time.

## Block Schema

Blocks that are sent to this function need to follow a specific structure in order to be dealt with effectively:

```json
{
  "block": {
    "response": <response input by user on the web app>,
    ""
    "gradingFunction": <grading function name>,
    "algorithmPipeline": [
      {
        "algorithmFunction": <algorithm function name>,
        "props": <optional function props>
      },
      ...
    ]
  }
}

```
