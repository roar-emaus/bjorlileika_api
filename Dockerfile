# Use alpine:latest as base image
FROM docker.io/library/alpine:latest

# Set the working directory to /bjorlileika_api
WORKDIR /bjorlileika_api

# Set environment variable DATA_PATH
ENV DATA_PATH=/bjorlileika_api/data/

# Install git, python3, and pip, then install the required Python packages
RUN apk add --no-cache git python3 py3-pip \
    && pip3 install uvicorn[standard] fastapi pydantic gunicorn

# Clone the Git repository
RUN git clone https://github.com/roar-emaus/bjorlileika_api.git .

# Set the default command to run when starting the container
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "api:api", "--bind", "0.0.0.0:80"]
