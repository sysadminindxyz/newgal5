# Use an official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app files into the container
COPY . .

# Start the Streamlit app when the container runs
CMD ["streamlit", "run", "test5.py", "--server.port=8501", "--server.address=0.0.0.0"]
