# Use Python image
FROM python:3.9

# Create working directory
WORKDIR /code

# Copy requirements and install
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy all files
COPY . .

# Start the bot (Flask + Bot)
CMD ["python", "app.py"]
