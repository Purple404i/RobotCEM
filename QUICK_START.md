# 🚀 RobotCEM Quick Start Guide

This guide will help you get RobotCEM up and running in a local Docker environment with the Aurora LLM and Blender simulation.

## 📋 Prerequisites

- **Docker & Docker Compose** installed.
- **NVIDIA Container Toolkit** (if you want GPU acceleration for Ollama and Blender).

## 🛠️ Installation

1.  **Clone the Repository** (including LEAP71 submodules):
    ```bash
    git clone --recurse-submodules https://github.com/Purple404i/RobotCEM.git
    cd RobotCEM
    ```

2.  **Start Services**:
    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```

3.  **Setup the Aurora Model**:
    RobotCEM uses the fine-tuned Aurora model via Ollama. You need to pull it once:
    ```bash
    docker exec -it robotcem-ollama-1 ollama run aurora
    ```
    *If 'aurora' is not yet on the public library, you can create it using a Modelfile:*
    ```bash
    # Inside the container or mapped volume
    ollama create aurora -f /app/backend/training/Modelfile
    ```

## 💻 Usage

### 1. Access the Studio UI
Open your browser to `http://localhost:3000`. This is the React-based design studio where you can:
- Enter natural language prompts.
- View 3D models (STL).
- Inspect the Bill of Materials (BOM).
- See the LLM's thinking process.

### 2. Basic Design Prompt
In the prompt bar, try:
> "Design a lightweight robotic gripper for picking up delicate biological samples. It should use a lattice infill for weight reduction and fit a standard MG996R servo."

### 3. The Design Loop
Once you submit a prompt:
1.  **Aurora** parses the requirements.
2.  **Market Scraper** finds the MG996R servo and other parts.
3.  **PicoGK** generates the 3D geometry with lattice infill.
4.  **Blender** runs a physics simulation to check if the gripper can hold a sample.
5.  **Aurora** analyzes the simulation result.
6.  If it fails (e.g., sample drops), Aurora updates the design and **re-runs** the loop.

## 🧪 Development & API

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Manual Generation Trigger
```bash
curl -X POST http://localhost:8000/api/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "3-DOF robotic arm"}'
```

## 📁 Key Directories

- `backend/`: Python source code (FastAPI, LLM logic).
- `frontend/`: React source code (Vite, Tailwind).
- `docker/`: Dockerfiles and Compose configuration.
- `scripts/`: Physics simulation scripts for Blender.

---

**Next Step**: Read the [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) to understand the interdisciplinary design loop in detail.
