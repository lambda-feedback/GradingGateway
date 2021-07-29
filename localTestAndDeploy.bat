docker container stop local-grading-container
docker build -t grading-gateway:test .
docker container run -d -p 9000:8080 --rm --name local-grading-container --env-file dev.env grading-gateway:test
docker container logs -f local-grading-container
