# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the ports for Streamlit and Prometheus metrics
EXPOSE 8501
EXPOSE 8001

# Run the application with metrics server pre-started
CMD ["python", "start.py"]