"""
Simple Example - Spring-Ready FastAPI Application

Shows how easy it is to:
1. Add Spring Boot ecosystem support (Eureka, Config Server, Actuator)
2. Create custom Prometheus metrics
3. Add new API endpoints

Run with:
    export EUREKA_SERVER_URL=http://10.10.0.1:8761/eureka/
    python example.py
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI
from spring_ready import SpringReadyApp

# Step 1: Configure logging (optional - enables /actuator/logfile auto-detection)
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Step 2: Create FastAPI app
app = FastAPI(title="My Microservice", version="1.0.0")

# Step 3: Add Spring-Ready (Eureka + Config Server + Actuator endpoints)
spring_app = SpringReadyApp(
    fastapi_app=app,
    instance_ip="10.10.0.10" # The instance server IP address (Where the app is running)
)

# Step 4: Create custom Prometheus metrics (super easy!)
request_counter: Any = None
processing_time: Any = None

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # Start Spring integration
    spring_app.start()

    # Set up custom metrics
    global request_counter, processing_time
    request_counter = spring_app.create_counter(
        'my_api_requests_total',
        'Total API requests',
        ['endpoint']
    )
    processing_time = spring_app.create_histogram(
        'my_api_processing_seconds',
        'API processing time',
        ['endpoint']
    )

    yield
    spring_app.shutdown()

app.router.lifespan_context = lifespan


# Step 5: Add your API endpoints
@app.get("/")
async def root():
    """Simple root endpoint"""
    if request_counter:
        request_counter.labels(endpoint='/').inc()

    return {
        "service": spring_app.app_name,
        "message": "Hello from Spring-Ready Python!"
    }


@app.get("/api/hello/{name}")
async def hello(name: str):
    """Greeting endpoint with Prometheus metrics"""
    import time

    # Track this request
    if request_counter:
        request_counter.labels(endpoint='/api/hello').inc()

    start = time.time()

    # Your business logic here
    greeting = os.getenv("GREETING_PREFIX", "Hello")
    response = {"message": f"{greeting}, {name}!"}

    # Record processing time
    if processing_time:
        processing_time.labels(endpoint='/api/hello').observe(time.time() - start)

    return response


@app.post("/api/data")
async def create_data(item: dict):
    """Example POST endpoint"""
    if request_counter:
        request_counter.labels(endpoint='/api/data').inc()

    return {"status": "created", "item": item}


@app.get("/api/discover/{service_name}")
async def discover_service(service_name: str):
    """
    Discover a service from Eureka and get its URL.

    Example: GET /api/discover/config-server
    Returns the base URL of the service registered in Eureka.

    This is super easy! Just one line to get any service URL:
        url = spring_app.service_discovery.get_service_url("config-server")
    """
    try:
        # Simple one-liner to get service URL
        url = spring_app.service_discovery.get_service_url(service_name.upper())

        # You can also get detailed instance information
        instance = spring_app.service_discovery.get_instance(service_name.upper())

        return {
            "service": service_name,
            "url": url,
            "instance_id": instance.instance_id,
            "status": instance.status,
            "metadata": instance.metadata
        }
    except Exception as e:
        return {"error": str(e), "service": service_name}


@app.get("/api/services")
async def list_services():
    """
    List all services registered in Eureka.

    Example: GET /api/services
    Returns a list of all available services.
    """
    services = spring_app.service_discovery.list_services()
    return {
        "total": len(services),
        "services": services
    }



# That's it! You get for free:
# - Eureka service registration with heartbeat
# - Config Server integration
# - 20+ Spring Boot Actuator endpoints:
#   /actuator/health, /actuator/metrics, /actuator/prometheus
#   /actuator/logfile, /actuator/env, /actuator/loggers, etc.
# - Swagger UI at /docs
# - OpenAPI spec at /openapi.json

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=spring_app.app_port, log_level="info")