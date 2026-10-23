# Lightweight official Python base image
FROM python:3.11-slim

# Working directory inside the container
WORKDIR /app

# Install the Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit application
COPY . .

# Streamlit listens on port 8501
EXPOSE 8501

# Default backend address = backend container name on the shared Docker network
ENV BACKEND_URL=http://backend:7860

# Launch Streamlit on all interfaces; CORS/XSRF disabled so file upload works behind the Codespaces port-forwarding proxy
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
