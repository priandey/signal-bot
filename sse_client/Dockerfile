# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /sse

# Install the required Python packages
COPY . /sse

# Run the Python script when the container launches
RUN python3 -m pip install -r requirements.txt
