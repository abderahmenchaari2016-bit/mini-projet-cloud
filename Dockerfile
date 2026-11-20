# Start from a small official Python image.
FROM python:3.12-alpine

# Keep the app files together inside the image.
WORKDIR /app

# Install the packages listed by this project.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application into the image.
COPY app.py .

# Document the port used by the Flask application.
EXPOSE 8000

# Start the API when a container is launched.
CMD ["python", "app.py"]
