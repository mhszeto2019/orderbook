# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5002

# Command to run the server (replace with actual app for each service)
CMD ["gunicorn", "-k", "gevent", "-w", "1", "--max-requests", "1000", "--max-requests-jitter", "100", "-b", "0.0.0.0:5002", "app.okx.okx_spotprice_server:app"]
