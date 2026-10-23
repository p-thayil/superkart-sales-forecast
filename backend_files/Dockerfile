# Lightweight official Python base image
FROM python:3.13-slim

# libgomp1 = OpenMP runtime required by XGBoost on slim images
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# Working directory inside the container
WORKDIR /app

# Install the Python dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the API code and the serialized model
COPY . .

# The API listens on port 7860
EXPOSE 7860

# Serve the Flask app object 'superkart_api' (defined in app.py) with gunicorn: 4 workers, bound to all interfaces on port 7860
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "--timeout", "120", "app:superkart_api"]
