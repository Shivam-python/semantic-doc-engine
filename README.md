# semantic-doc-engine
RAG for reading PDF and answering questions from document context.

## Run with Docker

### Prerequisites
- Docker + Docker Compose (or Podman + podman-compose)
- Port `8000` (API), `6379` (Redis), and `6333`/`6334` (Qdrant) available on your machine

### 1) Start services
From the project root:

```bash
docker compose up -d --build
```

If you are using Podman:

```bash
podman-compose up -d --build
```

This starts:
- `api` (FastAPI)
- `worker` (Celery)
- `redis`
- `qdrant`

### 2) Verify the app is running

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

You can also open:
- `http://localhost:8000/`
- `http://localhost:8000/docs`

### 3) View logs

```bash
docker compose logs -f api worker
```

Podman equivalent:

```bash
podman-compose logs -f api worker
```

### 4) Stop services

```bash
docker compose down
```

Podman equivalent:

```bash
podman-compose down
```

### 5) Clean restart (optional)

```bash
docker compose down -v
docker compose up -d --build
```
