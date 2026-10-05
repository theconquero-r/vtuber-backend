FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements
COPY ./requirements.txt /code/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the app
COPY ./app /code/app

# HuggingFace spaces require running on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
