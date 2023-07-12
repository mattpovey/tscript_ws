# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /ts_flask_app

# Copy the current directory contents into the container at /ts_flask_app
COPY . /ts_flask_app

# Create the uploads directory
RUN mkdir uploads

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Install Git
RUN apt-get update && apt-get install -y git build-essential wget

# Clone the whisper.cpp repo
RUN git clone https://github.com/ggerganov/whisper.cpp whisper.cpp

# Configure whisper.cpp
WORKDIR /ts_flask_app/whisper.cpp/
RUN make

# Download whisper.cpp models
WORKDIR /ts_flask_app/whisper.cpp/models/
RUN ./download-ggml-model.sh small
RUN ./download-ggml-model.sh medium
RUN ./download-ggml-model.sh large

# Make port 80 available to the world outside this container
EXPOSE 8008

WORKDIR /ts_flask_app

# Run gunicorn when the container launches
CMD ["gunicorn", "-c", "gunicorn_conf.py", "tscript_ws:ts_flask_app"]
