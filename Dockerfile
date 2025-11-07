FROM python:3.11-slim

LABEL maintainer="your-email@example.com"
LABEL description="Spring-Ready Python Microservice"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables (can be overridden)
ENV SPRING_APPLICATION_NAME=python-service
ENV APP_PORT=8080
ENV SPRING_PROFILES_ACTIVE=production
ENV EUREKA_SERVER_URL=http://eureka:8761/eureka/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/actuator/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "example:app", "--host", "0.0.0.0", "--port", "8080"]