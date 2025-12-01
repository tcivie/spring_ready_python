# Spring-Ready Python

Make your Python FastAPI app work seamlessly with Spring Boot ecosystem: Eureka, Config Server, Spring Boot Admin, and Prometheus.

## Why This Exists

You have a Spring Boot microservices architecture with Eureka, Config Server, Spring Boot Admin, and Prometheus monitoring. You want to add a Python service but keep everything working together. This library makes that dead simple.

## Features

✅ **Eureka Service Registration** - Automatic registration with heartbeat  
✅ **Config Server Integration** - Load config from Spring Cloud Config with Eureka discovery  
✅ **Actuator Endpoints** - `/actuator/health`, `/actuator/info`, `/actuator/prometheus`  
✅ **FastAPI Integration** - Drop-in support for FastAPI apps  
✅ **Fail-Fast Behavior** - Matches Spring Boot's startup failure handling  
✅ **Exponential Backoff Retry** - Retry logic for Eureka and Config Server  
✅ **Zero Magic** - Own implementation, no hidden dependencies

## Installation

```bash
pip install spring-ready-python
```

Optional dependencies:
```bash
# For Config Server support
pip install spring-config-client-python

# For Prometheus metrics
pip install prometheus-client
```

## Quick Start

```python
from spring_ready import SpringReadyApp
from fastapi import FastAPI

# Create FastAPI app
app = FastAPI()

# Add Spring integration
spring_app = SpringReadyApp(app)
spring_app.start()

# Your routes
@app.get("/")
def read_root():
    return {"message": "Hello from Spring-Ready Python!"}

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

That's it. Your app now:
- Registers with Eureka
- Loads config from Config Server (discovered via Eureka)
- Exposes `/actuator/health`, `/actuator/info`, `/actuator/prometheus`
- Shows up in Spring Boot Admin

## Configuration

Set via environment variables (matching Spring Boot conventions):

```bash
# Application
SPRING_APPLICATION_NAME=my-python-service
APP_PORT=8080
SPRING_PROFILES_ACTIVE=production

# Eureka
EUREKA_SERVER_URL=http://eureka:8761/eureka/
EUREKA_INSTANCE_IP=192.168.1.100  # Optional: custom IP for registration
EUREKA_INSTANCE_HOSTNAME=my-service.example.com  # Optional: custom hostname

# Config Server (optional - will be discovered from Eureka)
CONFIG_SERVER_URI=http://config-server:8888
CONFIG_SERVER_USERNAME=admin
CONFIG_SERVER_PASSWORD=secret
```

### Environment Variables Reference

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SPRING_APPLICATION_NAME` | Application name | `python-service` | `my-python-service` |
| `APP_PORT` | Application port | `8080` | `8080` |
| `SPRING_PROFILES_ACTIVE` | Active profile | `default` | `production` |
| `EUREKA_SERVER_URL` | Eureka server URL(s) | `http://localhost:8761/eureka/` | `http://eureka:8761/eureka/` |
| `EUREKA_INSTANCE_IP` | Custom IP for registration | Auto-detected | `192.168.1.100` |
| `EUREKA_INSTANCE_HOSTNAME` | Custom hostname | Auto-detected | `my-service.local` |
| `EUREKA_INSTANCE_SECURE` | Register with HTTPS URLs | `false` | `true` |
| `CONFIG_SERVER_URI` | Config Server URL | Discovered from Eureka | `http://config:8888` |
| `CONFIG_SERVER_SERVICE_ID` | Config Server service ID | `CONFIG-SERVER` | `CONFIG-SERVER` |
| `CONFIG_SERVER_USERNAME` | Config Server username | None | `admin` |
| `CONFIG_SERVER_PASSWORD` | Config Server password | None | `secret` |

## Docker Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV SPRING_APPLICATION_NAME=my-service
ENV EUREKA_SERVER_URL=http://eureka:8761/eureka/
ENV SPRING_PROFILES_ACTIVE=production

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
services:
  my-service:
    build: .
    environment:
      - EUREKA_SERVER_URL=http://eureka:8761/eureka/
      - SPRING_PROFILES_ACTIVE=production
    ports:
      - "8080:8080"
```

## Advanced Usage

### Custom Health Checks

```python
from spring_ready import SpringReadyApp

spring_app = SpringReadyApp(app)
spring_app.start()

# Add custom health check
def check_database():
    # Your database check logic
    return database.is_connected()

spring_app.health_endpoint.add_check("database", check_database)
```

### Service Discovery

```python
# Find another service registered in Eureka
config_server_url = spring_app.service_discovery.get_service_url("CONFIG-SERVER")

# Get all instances of a service
instances = spring_app.service_discovery.get_instances("my-other-service")

for instance in instances:
    print(f"Instance: {instance.base_url}")
```

### Manual Configuration

```python
from spring_ready import SpringReadyApp

spring_app = SpringReadyApp(
    app=app,
    app_name="my-service",
    app_port=8080,
    eureka_servers=["http://eureka1:8761/eureka/", "http://eureka2:8761/eureka/"],
    profile="production",
    fail_fast=True,
    prefer_ip_address=True
)
spring_app.start()
```

### Custom IP Address Registration

```python
from spring_ready import SpringReadyApp

# Specify a custom IP address for Eureka registration
# Useful in Docker/Kubernetes when you need to advertise a specific IP
spring_app = SpringReadyApp(
    app=app,
    app_name="my-service",
    instance_ip="192.168.1.100",  # Custom IP address
    instance_hostname="my-service.example.com"  # Optional: custom hostname
)
spring_app.start()
```

Or via environment variables:
```bash
export EUREKA_INSTANCE_IP=192.168.1.100
export EUREKA_INSTANCE_HOSTNAME=my-service.example.com
```

### HTTPS Registration (Secure Mode)

When your application uses HTTPS, you need to register with HTTPS URLs in Eureka so that Spring Boot Admin and other services can connect to it correctly.

```python
from spring_ready import SpringReadyApp

# Register with HTTPS URLs in Eureka
spring_app = SpringReadyApp(
    app=app,
    app_name="my-service",
    app_port=8443,
    secure=True  # Register with https:// URLs
)
spring_app.start()
```

Or via environment variable:
```bash
export EUREKA_INSTANCE_SECURE=true
```

When `secure=True`:
- The `homePageUrl`, `statusPageUrl`, and `healthCheckUrl` will use `https://`
- The `securePort` will be enabled and set to your `app_port`
- The regular `port` will be disabled

This is equivalent to Spring Boot's:
```yaml
eureka:
  instance:
    secure-port-enabled: true
    non-secure-port-enabled: false
```

## How It Works

### Startup Sequence

1. **Eureka Registration**: Registers with Eureka (with retry/backoff)
2. **Config Discovery**: Discovers Config Server from Eureka
3. **Config Loading**: Loads configuration into `os.environ`
4. **Actuator Setup**: Exposes health, info, and metrics endpoints
5. **Heartbeat**: Starts background thread for Eureka heartbeats (every 30s)

### Shutdown Sequence

1. Stops heartbeat thread
2. Deregisters from Eureka
3. Clean exit

### Behavior Matching Spring Boot

| Feature | Spring Boot | spring-ready-python |
|---------|-------------|---------------------|
| Fail-fast on startup | ✓ | ✓ |
| Exponential backoff retry | ✓ | ✓ |
| Eureka heartbeat (30s) | ✓ | ✓ |
| Config Server discovery | ✓ | ✓ |
| Actuator endpoints | ✓ | ✓ |
| Graceful shutdown | ✓ | ✓ |

## Actuator Endpoints

### GET /actuator/health

Returns application health status:

```json
{
  "status": "UP",
  "components": {
    "diskSpace": {"status": "UP"},
    "eureka": {"status": "UP"},
    "ping": {"status": "UP"}
  }
}
```

### GET /actuator/info

Returns application metadata:

```json
{
  "app": {
    "name": "my-python-service",
    "version": "1.0.0"
  },
  "python": {
    "version": "3.11.5",
    "runtime": {
      "name": "CPython",
      "version": "3.11.5"
    }
  }
}
```

### GET /actuator/prometheus

Returns Prometheus metrics in exposition format:

```
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",version="3.11.5"} 1.0
...
```

## Troubleshooting

### No Registration Attempts to Eureka Server

**Symptom**: You don't see any connection attempts to your Eureka server in logs or network monitoring.

**Cause**: The application is likely using the default Eureka URL (`http://localhost:8761/eureka/`) instead of your server.

**Solution**:

1. **Set the environment variable** (Recommended):
   ```bash
   export EUREKA_SERVER_URL=http://10.10.0.1:8761/eureka/
   python your_app.py
   ```

2. **Or pass it explicitly in code**:
   ```python
   spring_app = SpringReadyApp(
       app,
       eureka_servers=["http://10.10.0.1:8761/eureka/"]
   )
   ```

3. **Verify your configuration**:
   ```python
   import os
   print(f"EUREKA_SERVER_URL: {os.getenv('EUREKA_SERVER_URL')}")
   ```

4. **Check the startup logs**: Look for this message:
   ```
   INFO:spring_ready.core:Configured Eureka server(s): http://10.10.0.1:8761/eureka/
   ```

   If you see:
   ```
   WARNING:spring_ready.core:Using default Eureka server URL (http://localhost:8761/eureka/)
   ```
   Then you need to set `EUREKA_SERVER_URL`.

5. **Enable debug logging** to see detailed registration attempts:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

6. **Verify network connectivity**:
   ```bash
   curl http://10.10.0.1:8761/eureka/apps
   ```
   Should return XML/JSON with registered applications.

**Common mistakes**:
- Forgetting to set `EUREKA_SERVER_URL` in Docker/Kubernetes deployments
- Setting the variable in your IDE but not in the runtime environment
- Using `localhost` when running in containers (use service names or IPs instead)

### Eureka Registration Fails

Check Eureka server is reachable:
```bash
curl http://eureka:8761/eureka/apps
```

Set `fail_fast=False` to start anyway:
```python
spring_app = SpringReadyApp(app, fail_fast=False)
```

### Config Server Not Found

Ensure Config Server is registered in Eureka:
```bash
curl http://eureka:8761/eureka/apps/CONFIG-SERVER
```

Or provide direct URL:
```bash
export CONFIG_SERVER_URI=http://config-server:8888
```

### Port Already in Use

Change the port:
```python
spring_app = SpringReadyApp(app, app_port=8081)
```

Or via environment:
```bash
export APP_PORT=8081
```

## Differences from Spring Boot

| Aspect | Spring Boot | Python |
|--------|-------------|---------|
| Metrics names | `jvm.memory.used` | `process_virtual_memory_bytes` |
| Runtime info | Java/JVM | Python/CPython |
| Config refresh | `/actuator/refresh` | Not supported (restart required) |
| Auto-configuration | Annotations | Explicit initialization |

## Requirements

- Python 3.9+
- FastAPI
- requests

Optional:
- `spring-config-client-python` for Config Server support
- `prometheus-client` for metrics

## License

MIT

## Contributing

Contributions welcome! This library is intentionally simple and focused. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Comparison with Spring Boot

```kotlin
// Spring Boot (Kotlin)
@SpringBootApplication
@EnableDiscoveryClient
class MyApplication

// Configuration in application.yml
```

```python
# Python equivalent
from spring_ready import SpringReadyApp
from fastapi import FastAPI

app = FastAPI()
spring_app = SpringReadyApp(app)
spring_app.start()

# Configuration from environment variables
```

---

**Note**: This library focuses on making Python apps work with existing Spring Boot infrastructure. It's not a replacement for Spring Boot itself.
