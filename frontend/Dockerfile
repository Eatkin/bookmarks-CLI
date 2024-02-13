FROM python:3.10.6-buster

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Copy the contents of frontend to app
COPY bookmarks-414106-82ffd7e77bda.json /app/credentials.json
COPY . /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV SERVICE_WORKER=/app/credentials.json

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
