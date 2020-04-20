FROM python:3.7-slim-buster

# Make working directories
RUN  mkdir -p /home/project-api
WORKDIR /home/project-api/

# Copy application requirements file to the created working directory
COPY requirements.txt .

# Install application dependencies from the requirements file
RUN pip install -r requirements.txt

# Copy every file in the source folder to the created working directory
COPY  . .

# Run the python application
CMD ["python", "main.py"]