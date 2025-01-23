# Use the official Python 3.12.3 base image
FROM python:3.12.3-slim

# Set environment variables to prevent Python from writing pyc files to disc
# and to make Python output everything to the console (for debugging)
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the required Python packages inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory to the container
COPY . .

# Expose the port that FastAPI will run on (default: 8000)
EXPOSE 8080

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]