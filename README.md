# 🤖 RobotCEM - Interdisciplinary AI-Powered Computational Engineering

RobotCEM is an advanced system for designing, simulating, and optimizing robotic components. It combines the **Aurora** technical AI model with **PicoGK** (voxel-based geometry) and **Blender** (physics simulation) to create a scientifically accurate design-simulate-fix loop.

## 🌟 Key Features

- **Aurora Technical AI**: A fine-tuned LLM specialized in robotics, physics, biology, and materials science.
- **PicoGK Integration**: Generates complex, high-performance 3D geometry using LEAP71's ShapeKernel and LatticeLibrary.
- **Blender Physics Simulation**: Automatically validates designs in a physics engine to ensure stability and functionality.
- **Automated "Fix" Loop**: If a design fails simulation or physics validation, the AI analyzes the failure and iteratively improves the design.
- **Interdisciplinary Sourcing**: Integrated market scraper (DDGS) to find real-world parts like servos, bearings, and specialized biological materials.
- **Local-First & Private**: Runs entirely on your own hardware via Docker and Ollama—no external API keys required.

## 🏗️ System Architecture

RobotCEM follows a scientifically grounded 8-step workflow:

1.  **Parse Prompt**: Aurora analyzes natural language to extract engineering requirements.
2.  **Source Components**: Market search for non-printable parts (servos, sensors, etc.).
3.  **Recommend Geometry**: Mapping requirements to PicoGK BaseShapes.
4.  **Lattice Optimization**: Generating internal structures for weight reduction (-40%).
5.  **Physics Validation**: Initial structural and thermal checks.
6.  **Code Generation**: Aurora writes specific C# (PicoGK) and Python (Blender) scripts.
7.  **Simulation & Analysis**: Executing the 3D generation and Blender physics check.
8.  **Automated Refinement**: Recursive improvement if validation/simulation fails.

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**
- **NVIDIA GPU** (recommended for Ollama/Blender performance)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone --recurse-submodules https://github.com/Purple404i/RobotCEM.git
    cd RobotCEM
    ```

2.  **Start the infrastructure**:
    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```

3.  **Setup Aurora Model**:
    ```bash
    docker exec -it robotcem-ollama-1 ollama run aurora
    ```
    *(Note: The model will be pulled/configured on first run)*

### Access

- **Frontend Studio**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Ollama API**: `http://localhost:11434`

---

## 🧬 Interdisciplinary Domains

RobotCEM isn't just for mechanical parts. Aurora's knowledge spans:

-   **Robotics**: Kinematics, actuators, sensor integration, power systems.
-   **Biology**: Biomechanics, bioelectronics, tissue engineering, molecular dynamics.
-   **Materials**: Battery chemistry, polymers, composites, high-temp alloys.
-   **Mathematics**: Control theory, optimization, differential equations.

---

## 🛠️ Developer Tools

### Manual Design Trigger

```python
import requests

# Aurora will generate the specs, PicoGK code, and Blender simulation
response = requests.post('http://localhost:8000/api/generate', json={
    "prompt": "Design a bio-inspired 4-DOF robotic leg with carbon fiber lattice infill"
})

job_id = response.json()['job_id']
print(f"Design process started: {job_id}")
```

### Inactivity Analysis
The system monitors for 5 minutes of inactivity. If a user stops editing a model, Aurora automatically triggers a full re-analysis and simulation to verify the latest changes.

---

## 📁 Project Structure

-   `backend/`: FastAPI server, LLM orchestration, and PicoGK/Blender bridges.
-   `frontend/`: React-based studio with 3D preview and specification panels.
-   `csharp_runtime/`: The PicoGK execution environment with LEAP71 submodules.
-   `scripts/`: Utility scripts for simulation and environment setup.
-   `docker/`: Container definitions for a seamless local setup.

---

## 📄 License

See [License.txt](License.txt) for details.

**Built with ❤️ by the RobotCEM Team and the LEAP71 Community.**
