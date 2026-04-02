FROM python:3.11.9-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY . .

# Make the run.sh script executable
RUN chmod +x run.sh

# Expose the port
EXPOSE 8000

# Set run.sh as the entrypoint for the container
ENTRYPOINT ["./run.sh"]
