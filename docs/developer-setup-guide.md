# PowerRAG Source Code Deployment Guide

> This guide documents the complete process of deploying PowerRAG from source code, using SeekDB (OceanBase) Docker container for the database, suitable for local development environments.

---

## Table of Contents

- [Quick Start](#quick-start)
- [1. Prerequisites](#1-prerequisites)
- [2. Database Deployment (SeekDB)](#2-database-deployment-seekdb)
- [3. Backend Deployment](#3-backend-deployment)
- [4. Frontend Deployment](#4-frontend-deployment)
- [5. Troubleshooting](#5-troubleshooting)

---

## Quick Start

Here are the quick reference commands for a complete deployment:

```bash
# 1. Start SeekDB database
docker run -d --name powerrag-seekdb \
  -p 2881:2881 \
  -e ROOT_PASSWORD=powerrag \
  -e INIT_SCRIPTS_PATH=/root/boot/init.d \
  -v $(pwd)/docker/oceanbase/init.d:/root/boot/init.d \
  oceanbase/seekdb:1.0.0.0-100000262025111218

# 2. Wait for database to be ready & create databases
sleep 60
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e \
  "CREATE DATABASE IF NOT EXISTS powerrag; CREATE DATABASE IF NOT EXISTS powerrag_doc;"

# 3. Install Python dependencies
uv sync --python 3.12 --all-extras

# 4. Download models and NLP resources
docker pull infiniflow/ragflow_deps:latest
bash set_backend_deps.sh

# 5. Start backend
source .venv/bin/activate
export PYTHONPATH=$(pwd)
bash docker/launch_backend_service.sh &

# 6. Install frontend dependencies
cd web
npm install

# 7. Start frontend
npm run dev &

# 8. Access
# Frontend: http://localhost:9222
# API: http://localhost:9380
```

---

## 1. Prerequisites

| Component | Version Requirement | Notes |
|-----------|-------------------|-------|
| **OS** | Linux (x86_64) | Tested on AlmaLinux 8 (kernel 5.10) |
| **Python** | ≥ 3.12, < 3.15 | Recommended 3.12.x |
| **uv** | ≥ 0.9.x | Python package manager |
| **Node.js** | ≥ 22.x | Frontend build |
| **npm** | ≥ 10.x | Frontend package manager |
| **Docker** | ≥ 20.x | For running SeekDB database |
| **Disk Space** | ≥ 50GB | Database + model files + dependencies |
| **Memory** | ≥ 16GB | SeekDB recommends 10GB+, application services 4GB+ |

---

## 2. Database Deployment (SeekDB)

### 2.1 Start SeekDB Container

```bash
docker run -d \
  --name powerrag-seekdb \
  -p 2881:2881 \
  -e ROOT_PASSWORD=powerrag \
  -e INIT_SCRIPTS_PATH=/root/boot/init.d \
  -v $(pwd)/docker/oceanbase/init.d:/root/boot/init.d \
  oceanbase/seekdb:1.0.0.0-100000262025111218
```

> **Notes**:
> - `ROOT_PASSWORD=powerrag`: Sets the database root password, must match the configuration in `conf/service_conf.yaml`
> - The initialization script `docker/oceanbase/init.d/vec_memory.sql` executes `ALTER SYSTEM SET ob_vector_memory_limit_percentage = 30;` to allocate memory for vector search
> - Port `2881` is OceanBase's MySQL protocol port

### 2.2 Wait for Database to Be Ready

SeekDB startup takes approximately 30-60 seconds. Verify with:

```bash
# Check container health status
docker ps --filter name=powerrag-seekdb --format 'table {{.Names}}\t{{.Status}}'

# Test connection
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e "SELECT 1;"
```

### 2.3 Create Databases

```bash
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e "
  CREATE DATABASE IF NOT EXISTS powerrag;
  CREATE DATABASE IF NOT EXISTS powerrag_doc;
"
```

---

## 3. Backend Deployment

### 3.1 Install Python Dependencies

```bash
cd /path/to/powerrag
uv sync --python 3.12 --all-extras
```

> **Estimated Time**: First-time installation takes approximately 10-20 minutes (depending on network speed).

### 3.2 Download Models and NLP Resources

PowerRAG depends on multiple pre-trained models and NLP datasets. It's recommended to use the pre-built Docker image for quick access:

```bash
# Pull the dependencies image first
docker pull infiniflow/ragflow_deps:latest

# Execute the dependency copy script
bash set_backend_deps.sh
```

This script copies the following resources from the `infiniflow/ragflow_deps:latest` image:

| Resource | Target Path | Purpose |
|----------|-------------|---------|
| HuggingFace Deep Document Models | `rag/res/deepdoc/` | Document layout analysis |
| XGBoost Text Concatenation Model | `rag/res/deepdoc/` | Text paragraph merging |
| BAAI/bge-large-zh-v1.5 | `~/.ragflow/` | Chinese vector embeddings |
| BCE Embedding | `~/.ragflow/` | Vector embeddings |
| NLTK Data | `nltk_data/` | Natural language processing |
| Tika Server | `tika-server-standard-3.2.3.jar` | Document parsing |
| tiktoken Encoding | `9b5ad71b2ce5302211f9c61530b329a4922fc6a4` | Token calculation |

### 3.3 Start Backend Services

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)

# Use the startup script (starts API Server, Task Executor, and Data Sync service)
bash docker/launch_backend_service.sh
```

After successful startup, the API Server listens on `http://0.0.0.0:9380` by default.

#### Verify Backend Service

```bash
curl -s http://localhost:9380/v1/system/healthz
# Expected: JSON response indicating health check passed
```

#### Backend Startup Log Notes

The following warnings may appear during normal startup and are expected:

| Log Message | Description |
|-------------|-------------|
| `term.freq is not supported` | OceanBase's full-text index doesn't support term frequency feature, doesn't affect functionality |
| `Realtime synonym is disabled, since no redis connection` | Redis not configured, real-time synonym update feature unavailable |
| `pthread_setaffinity_np failed` | ONNX Runtime thread affinity setting failed, no impact |

---

## 4. Frontend Deployment

### 4.1 Install Dependencies

```bash
cd web
npm install
```

> **Note**: The installation process automatically runs the Tailwind CSS plugin fix script (via `postinstall` hook) to fix known issues with the UmiJS Tailwind plugin. If you encounter Tailwind CSS generation failures, you can manually run:
> ```bash
> node scripts/fix-tailwindcss-plugin.js
> ```

### 4.2 Start Frontend Development Server

```bash
cd web
npm run dev
```

The frontend development server runs on `http://localhost:9222` by default (proxies API requests to backend port 9380).

---

## 5. Troubleshooting

### Q1: `download_deps.py` Download Timeout

**Cause**: Unable to directly access external URLs (Maven Central, HuggingFace, etc.)

**Solution**: Use `set_backend_deps.sh` to copy dependencies from Docker image:

```bash
docker pull infiniflow/ragflow_deps:latest
bash set_backend_deps.sh
```

---

### Q2: SeekDB Connection Error `Access denied`

**Cause**: Password mismatch or container not fully started

**Solution**:
1. Check container status: `docker ps --filter name=powerrag-seekdb`
2. Verify password matches startup parameter: `ROOT_PASSWORD=powerrag`
3. Wait for container healthcheck to pass before connecting

---

### Q3: Backend Startup Error `peewee.OperationalError: (1049, "Unknown database 'powerrag'")`

**Cause**: Database not created yet

**Solution**:

```bash
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e "
  CREATE DATABASE IF NOT EXISTS powerrag;
  CREATE DATABASE IF NOT EXISTS powerrag_doc;
"
```

---

### Q4: ONNX Runtime Error `pthread_setaffinity_np failed`

**Cause**: Some containerized or restricted Linux environments don't support thread affinity settings

**Solution**: This warning doesn't affect functionality and can be ignored.
