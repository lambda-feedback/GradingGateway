FROM public.ecr.aws/lambda/python:3.8

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy grading and handler code
COPY grade.py .
COPY lambda_function.py .

# Set the CMD to handler
CMD [ "lambda_function.handler" ]
