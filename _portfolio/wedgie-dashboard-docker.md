---
  layout: single
  title: "Wedgie Dashboard: Learning Docker"
  date: 2026-02-06
  description: "Building and deploying a Streamlit analytics platform with Docker containers"
  author_profile: true
  toc: true
  toc_sticky: true
  classes: wide
  tags:
    - docker
    - containers
    - deployment
    - streamlit
    - devops
    - python
  excerpt: "How Docker transformed a complex Streamlit app with multiple dependencies into a reproducible, portable
  analytics platform—and why containerization matters for data science projects."
---

  [<i class="fas fa-external-link-alt" aria-hidden="true"></i> View Live
  Dashboard](https://wedgie-tracker-dashboard.streamlit.app/){: .btn .btn--info}

  <style>
    .streamlit-container {
      border: 1px solid #ddd;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin: 2rem 0;
    }
    .dashboard-loading {
      text-align: center;
      padding: 2rem;
      color: #666;
      font-style: italic;
    }
  </style>

  <div class="streamlit-container">
    <div id="dashboard-loading" class="dashboard-loading">Loading interactive dashboard...</div>
    <iframe
      id="wedgie-dashboard"
      src="https://wedgie-tracker-dashboard.streamlit.app/?embed=true"
      width="100%"
      height="1200"
      frameborder="0"
      allowfullscreen="true"
      style="display:none;"
      onload="document.getElementById('dashboard-loading').style.display='none'; this.style.display='block';">
    </iframe>
  </div>

  ---

## Abstract

  The Wedgie Dashboard visualizes every NBA "wedgie" (when the ball gets stuck between the rim and backboard) through an
  interactive Streamlit application with court zone overlays, video integration, and advanced analytics. Built rapidly
  with Claude Code, the dashboard combines web scraping, NBA API enrichment, and Plotly visualizations into a cohesive
  analytics platform.

  But here's the challenge: **how do you deploy a multi-dependency Python application consistently across different
  environments?** The dashboard requires specific versions of Streamlit, Plotly, pandas, and the NBA API... each with their
  own transitive dependencies. It needs to run identically on my local Windows machine, a colleague's Mac, and a cloud
  Linux server. This is where I turned to Docker.

  This post isn't about how I built the dashboard's features (Claude Code handled most of that heavy lifting). Instead,
  it's a deep dive into **why I containerized the application** and **how Docker solves the problem** of different machines, different    outcomes that plagues data science deployments. I'll walk through Dockerfiles, multi-stage builds, volume mounts,
  and the transition from local development to cloud hosting.

## Key Contributions

  - **Dockerized Streamlit application** with reproducible builds
  - **Multi-stage Docker builds** for development vs. production
  - **Volume mounting strategy** for local data
  - **Docker Compose** for simplified workflows
  - **Deployment path** from local containers to Streamlit Cloud

  ---

## 1. The Dashboard

  Before diving into Docker, let me quickly highlight what makes this dashboard interesting:

### 1.1 What It Does

  The Wedgie Dashboard is an interactive analytics platform that:

  - **Visualizes 600+ wedgie events** on NBA court heatmaps with scatter, density, and hexbin modes
  - **Integrates video evidence** from YouTube, Cloudinary, and Instagram with click-to-watch functionality
  - **Defines 8 court zones** geometrically (Restricted Area, Paint, Corner 3s, Wing 3s, Straight-on 3, Midrange)
  - **Provides player profiles** with filterable video galleries and career statistics
  - **Analyzes patterns** through historical trends, shot clock pressure, and zone evolution charts

### 1.2 The Coolest Parts

  **Court Zone System**: Uses trigonometry to classify every shot into precise zones. The restricted area is an arc,
  wing threes are sectors based on angle calculations, and the system validates shot distances to prevent mismatches
  (like labeling a 40-foot shot as a "layup").

  **Video Integration**: Every wedgie links to video evidence. Click any scatter point or table row and watch the actual
   play. The system automatically selects the best source (Cloudinary MP4 > YouTube embed > Instagram link) with 100%
  coverage.

  **Smart Data Enrichment**: The NBA API doesn't have a "wedgie" event type, so the pipeline scrapes WedgieTracker.com,
  matches events to official shot data, and validates matches with distance-based scoring. A layup wedgie must be < 10
  feet, three-pointers must be 22-35 feet, etc. It's not perfect matching, since players miss multiple threes per game, but the logic covers most cases.

### 1.3 Built with Claude Code

  Full transparency: **Claude Code built about 80% of this dashboard**. I provided the architecture (zones, video,
  analytics) and Claude Code implemented:

  - Zone classification algorithms with geometric calculations
  - Video player components with fallback logic
  - Advanced analytics charts (historical trends, shot clock analysis)
  - UI polish (consolidating shot types, tab ideas)
  - Bug fixes (Plotly API updates, scatter plot click handling)

  The value I added was product thinking (what features matter?), data quality validation (improved shot matching
  algorithm), and understanding Docker deployment (which is what this post is really about).

  ---

## 2. Why Docker? The Deployment Problem

### 2.1 "Works on My Laptop"

  Here's the scenario every data scientist has experienced:

  **You**: "Check out this dashboard I built!"
  
  **Colleague**: "Okay, running `streamlit run app.py`..."
  
  **Terminal**: `ModuleNotFoundError: No module named 'nba_api'`
  
  **Colleague**: "Did you include a requirements.txt?"
  
  **You**: "Yes, run `pip install -r requirements.txt`"
  
  **Terminal**: `ERROR: Could not find a version that satisfies the requirement streamlit>=1.32.0`
  
  **Colleague**: "What Python version are you using?"
  
  **You**: "3.11"
  
  **Colleague**: "I'm on 3.9, maybe that's why..."
  
  **You**: "..."

  This is the **dependency nightmare**. Python applications rely on:

  - **The right Python version** (3.9 vs 3.11 vs 3.13)
  - **The right package versions** (Streamlit 1.32 has different APIs than 1.28)
  - **Transitive dependencies** (Plotly needs specific NumPy versions)
  - **System libraries** (some packages need gcc, system-level dependencies)
  - **Environment variables** (API keys, file paths)

  Even with a perfect `requirements.txt`, you're not guaranteed reproducibility because:

  - Your colleague might have conflicting packages already installed
  - System Python might differ from virtual env Python
  - OS-specific quirks (Windows vs. Mac vs. Linux)

### 2.2 The Docker Solution

  Docker solves this by packaging **everything** your application needs into a single container:

┌───────────────────────────────────────────┐
│             Docker Container              │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │      Your Application (app.py)      │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │         Python 3.11 Runtime         │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │          All Dependencies           │  │
│  │     (streamlit, plotly, pandas)     │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │           System Libraries          │  │
│  │           (gcc, git, etc.)          │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │              Linux OS               │  │
│  └─────────────────────────────────────┘  │
└───────────────────────────────────────────┘
  **Key Part**: A Docker container is like a lightweight virtual machine that includes the OS, runtime, dependencies,
   and application **but shares the host's kernel**, making it much faster than traditional VMs. To share a kernel means that the container stays lightweight by letting the host machine handle the core system tasks, allowing the app to start instantly and use fewer resources than booting up a VM. 

### 2.3 Why Docker for This Project

  For the Wedgie Dashboard specifically, Docker was essential because:

  **1. Complex dependency chain**:
  - `streamlit` requires specific `plotly` versions
  - `nba_api` has strict version requirements
  - `pandas` needs compatible `numpy`
  - All must work together without conflicts

  **2. Multiple data sources**:
  - Local CSV files in `data/processed/`
  - Cached NBA API responses in `data/cache/`
  - Configuration files with API settings

  **3. Portability goals**:
  - Run locally during development (Windows)
  - Deploy to cloud (Linux)
  - Share with collaborators (Mac, Linux, Windows)
  - Ensure reproducibility for future me

  ---

## 3. Docker Fundamentals

  Before diving into the implementation, I want to clarify core Docker concepts:

### 3.1 Images vs. Containers

<img width="1200" height="594" alt="image" src="https://github.com/user-attachments/assets/70129071-27be-453a-b0ec-d9c2838d4b99" />

*Figure 1: Images and Containers*

  **Image**: A blueprint or template (like a class in Object Oriented Programming)
  - Read-only filesystem snapshot
  - Contains OS, runtime, dependencies, application code
  - Built once, used many times
  - Versioned with tags (e.g., `wedgie-dashboard:latest`)

  **Container**: A running instance of an image (like an object in OOP)
  - Writable layer on top of the image
  - Isolated process with its own filesystem, network, process space
  - Can be started, stopped, deleted
  - Multiple containers can run from one image

### 3.2 Dockerfile

  A `Dockerfile` is a script that defines how to build an image:

  ```dockerfile
  # Start from a base image (Python 3.11 on Debian)
  FROM python:3.11-slim

  # Set working directory inside container
  WORKDIR /app

  # Copy requirements file
  COPY requirements.txt .

  # Install Python dependencies
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY . .

  # Expose port 8501 (Streamlit default)
  EXPOSE 8501

  # Command to run when container starts
  CMD ["streamlit", "run", "app.py"]
  ```

  Each line creates a layer. Docker caches layers, so if you only change app.py, it doesn't reinstall all
  dependencies. It just copies the new code.

### 3.3 Volumes

  The problem is that containers are temporary. Once you stop a container, that data written inside is lost.

  So what can you do? Well, volumes are a feature that can mount external data directories inside a container.

  <img width="800" height="400" alt="image" src="https://github.com/user-attachments/assets/034f3fdb-6176-4d05-a901-2746e6d5a676" />

  *Figure 2: How do volumes work?*

  ```dockerfile
  volumes:
    - ./data:/app/data  # Mount local data/ folder to container's /app/data
  ```

  Now when the container writes to /app/data, it's actually writing to your local ./data folder, which remains after the container stops.

### 3.4 Docker Compose

  Another problem that Docker sovles is simplifying the entire process of running a container. Take, for instance, a container with many options:

  ```ps
  docker run -p 8501:8501 -v ./data:/app/data -v ./cache:/app/cache --name wedgie-dashboard wedgie-image:latest
  ```

  To solve this problem, Docker Compose allows you to define an entire app stack in a single configuration file. Instead of the PS command above with options ontop of options, Docker makes it as easy as possible.

  ```YAML
  version: '3.8'
  services:
    dashboard:
      build: .
      ports:
        - "8501:8501"
      volumes:
        - ./data:/app/data
        - ./cache:/app/cache
  ```

  Now, all I need to do is just run: ```PS docker-compose up```

  ---
  4. Implementing Docker for the Wedgie Dashboard

  4.1 The Dockerfile

  Here's the actual Dockerfile for the project:

  # Use official Python runtime as base image
  FROM python:3.11-slim

  # Set working directory
  WORKDIR /app

  # Install system dependencies (if needed)
  RUN apt-get update && apt-get install -y \
      gcc \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements first (for layer caching)
  COPY requirements.txt .

  # Install Python dependencies
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY . .

  # Create data directories (ensure they exist)
  RUN mkdir -p data/raw data/processed data/cache

  # Expose Streamlit port
  EXPOSE 8501

  # Health check (optional but good practice)
  HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

  # Run Streamlit when container starts
  CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]

  Key decisions:

  1. python:3.11-slim base image:
  - slim variant is smaller than full Python image (saves 200+ MB)
  - Includes only essential system libraries
  - Trade-off: some packages with C extensions might need extra dependencies

  2. gcc installation:
  - Some Python packages (like pandas native extensions) require a C compiler
  - Installed at system level, then cleaned up to minimize image size

  3. Layer ordering:
  - requirements.txt copied before application code
  - Docker caches layers, so if you change app.py, it doesn't reinstall dependencies
  - Only if requirements.txt changes do dependencies reinstall

  4. --server.address 0.0.0.0:
  - By default, Streamlit only binds to localhost (127.0.0.1)
  - Inside a container, you need 0.0.0.0 to accept connections from host machine
  - Without this, you couldn't access the dashboard from your browser

  4.2 The Docker Compose Configuration

  version: '3.8'

  services:
    dashboard:
      build:
        context: .
        dockerfile: Dockerfile
      container_name: wedgie-dashboard
      ports:
        - "8501:8501"
      volumes:
        # Mount data directories for persistence
        - ./data/raw:/app/data/raw
        - ./data/processed:/app/data/processed
        - ./data/cache:/app/data/cache
      environment:
        # Streamlit configuration
        - STREAMLIT_SERVER_PORT=8501
        - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      restart: unless-stopped
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
        interval: 30s
        timeout: 10s
        retries: 3

  Why Docker Compose?

  Before Docker Compose (manual commands):
  # Build image
  docker build -t wedgie-dashboard .

  # Run container with all options
  docker run -d \
    --name wedgie-dashboard \
    -p 8501:8501 \
    -v ./data/raw:/app/data/raw \
    -v ./data/processed:/app/data/processed \
    -v ./data/cache:/app/data/cache \
    --restart unless-stopped \
    wedgie-dashboard

  # Check logs
  docker logs wedgie-dashboard

  # Stop container
  docker stop wedgie-dashboard

  # Remove container
  docker rm wedgie-dashboard

  With Docker Compose (simple commands):
  # Build and start
  docker-compose up --build

  # Stop
  docker-compose down

  # View logs
  docker-compose logs

  # Rebuild
  docker-compose up --build

  Much cleaner, and the configuration is version-controlled in docker-compose.yml.

  4.3 Volume Mounting Strategy

<img width="800" height="400" alt="image" src="https://github.com/user-attachments/assets/a0294526-a19c-483c-b97a-72ad8c4f5479" />
*Figure 1: Docker Volume, visualized*

  The volume mounts solve three problems:

  1. Data persistence:
  - ./data/processed:/app/data/processed
  When the enrichment pipeline writes to data/processed/wedgies_enriched.csv, it writes to your local filesystem, not
  inside the ephemeral container.

  2. Cache reuse:
  - ./data/cache:/app/data/cache
  NBA API responses are cached locally. When you rebuild the container, the cache persists, avoiding redundant API
  calls.

  3. Local development:
  # Optional: for live code editing
  - ./app.py:/app/app.py
  - ./dashboard:/app/dashboard
  During development, you can edit code locally and see changes without rebuilding. (This adds a "hot reload"
  development workflow.)

  4.4 Multi-Stage Builds (Advanced)

  For production deployments, you can optimize image size with multi-stage builds:

  # Stage 1: Build dependencies
  FROM python:3.11-slim AS builder

  WORKDIR /app
  COPY requirements.txt .

  # Install dependencies in a virtual environment
  RUN python -m venv /opt/venv
  ENV PATH="/opt/venv/bin:$PATH"
  RUN pip install --no-cache-dir -r requirements.txt

  # Stage 2: Production image
  FROM python:3.11-slim

  WORKDIR /app

  # Copy only the virtual environment from builder
  COPY --from=builder /opt/venv /opt/venv
  ENV PATH="/opt/venv/bin:$PATH"

  # Copy application code
  COPY . .

  EXPOSE 8501
  CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]

  Why multi-stage?

  - Stage 1 includes build tools (gcc, pip cache)
  - Stage 2 only includes the virtual environment and code
  - Final image is ~30% smaller because build tools aren't included
  - Production image has smaller attack surface

  For this project, I kept it simple with a single-stage build, but multi-stage is best practice for production.

  ---
  5. Workflow: From Docker to Cloud

  5.1 Local Development Workflow

  Step 1: Clone the repository
  git clone https://github.com/tommygarner/wedgie-tracker-dashboard.git
  cd wedgie-tracker-dashboard

  Step 2: Build and run with Docker Compose
  docker-compose up --build

  This:
  - Builds the Docker image from Dockerfile
  - Installs all dependencies inside the container
  - Mounts data directories
  - Starts Streamlit on http://localhost:8501

  Step 3: Access the dashboard
  Open browser to http://localhost:8501 — the dashboard is running inside Docker but accessible from your host machine.

  Step 4: Make changes (optional)
  Edit code locally. If you mounted volumes for code (./app.py:/app/app.py), Streamlit auto-reloads. Otherwise, restart:
  docker-compose restart

  Step 5: Stop the container
  docker-compose down

  5.2 Running the Data Pipeline in Docker

  The enrichment pipeline can also run inside the container:

  # Run pipeline inside the running container
  docker-compose exec dashboard python -m scraper.run_pipeline --skip-scrape

  # Or run as a one-off command
  docker-compose run dashboard python -m scraper.run_pipeline

  This ensures the pipeline runs with the exact same dependencies as the dashboard, avoiding "works in pipeline but not
  in dashboard" issues.

  5.3 Transitioning to Cloud Deployment

  Docker's portability shines here: the same image that runs locally can deploy to cloud providers.

  Option 1: Streamlit Cloud (Simplest)

  Streamlit Cloud doesn't use Docker directly, but reads requirements.txt:
  # Push to GitHub
  git push origin main

  # On Streamlit Cloud dashboard:
  # 1. Connect GitHub repo
  # 2. It automatically detects requirements.txt
  # 3. Builds and deploys

  Advantage: Free, zero configuration, automatic rebuilds on push.

  Disadvantage: Less control over environment, can't run scraping pipeline (cloud runners have limited compute).

  Option 2: Deploy Docker to Cloud VPS (Digital Ocean, AWS EC2, etc.)

  # On cloud server:
  git clone https://github.com/tommygarner/wedgie-tracker-dashboard.git
  cd wedgie-tracker-dashboard

  # Install Docker (one-time setup)
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh

  # Run the dashboard
  docker-compose up -d

  # Access via server IP
  http://your-server-ip:8501

  Advantage: Full control, can run data pipeline, persistent storage.

  Disadvantage: Costs money, requires server management.

  Option 3: Container Registry + Orchestration (Production Scale)

  # Build and tag image
  docker build -t your-dockerhub-username/wedgie-dashboard:latest .

  # Push to Docker Hub
  docker push your-dockerhub-username/wedgie-dashboard:latest

  # Deploy to Kubernetes, AWS ECS, Google Cloud Run, etc.
  kubectl apply -f deployment.yaml

  Advantage: Scales to many users, load balancing, zero-downtime deployments.

  Disadvantage: Complex, overkill for a personal project.

  My Choice: For this project, I use Streamlit Cloud for public access (simple, free) and local Docker for development
  and data pipeline work (full control, fast iteration).

  ---
  6. Docker Best Practices I Learned

  6.1 Keep Images Small

  Before (naive approach):
  FROM python:3.11  # Full image: 1.2 GB

  After (optimized):
  FROM python:3.11-slim  # Slim image: 180 MB

  Benefit: 85% size reduction means faster builds, pushes, and pulls.

  6.2 Use .dockerignore

  Just like .gitignore, .dockerignore prevents copying unnecessary files:

  # .dockerignore
  __pycache__/
  *.pyc
  .git/
  .vscode/
  .env
  data/cache/*
  venv/

  Before: Image includes 500 MB of cached API responses.
  After: Image only includes code, data persists via volumes.

  6.3 Layer Caching is Your Friend

  Bad (invalidates cache on every change):
  COPY . .
  RUN pip install -r requirements.txt

  Good (only reinstalls if requirements change):
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .

  Impact: Rebuilds take 5 seconds instead of 2 minutes when you only change code.

  6.4 Don't Run as Root

  By default, containers run as root, which is a security risk:

  # Create non-root user
  RUN useradd -m -u 1000 appuser && chown -R appuser /app
  USER appuser

  For this project, I skipped this (it's not internet-facing), but for production, always use non-root users.

  6.5 Health Checks for Reliability

  HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

  This lets Docker (and orchestrators like Kubernetes) detect if the app crashed and automatically restart it.

  ---
  7. Common Docker Debugging Scenarios

  7.1 "Container won't start"

  # Check logs
  docker-compose logs

  # Common causes:
  # - Port 8501 already in use
  # - Missing environment variables
  # - Syntax error in code

  Solution: Logs tell you exactly what failed. Fix the error, rebuild.

  7.2 "Can't access dashboard from browser"

  # Verify container is running
  docker-compose ps

  # Check port mapping
  # Should show: 0.0.0.0:8501->8501/tcp

  Common fix: Ensure --server.address 0.0.0.0 in Streamlit command.

  7.3 "Data not persisting"

  # Check if volumes are mounted
  docker inspect wedgie-dashboard | grep Mounts

  Solution: Verify docker-compose.yml has correct volume paths.

  7.4 "Module not found" inside container

  # Exec into container to debug
  docker-compose exec dashboard bash

  # Check if package is installed
  pip list | grep streamlit

  # If missing, rebuild
  docker-compose up --build

  7.5 "Works locally, fails in cloud"

  Common cause: Different base image or Python version between local and cloud.

  Solution: Pin versions in Dockerfile:
  FROM python:3.11.8-slim  # Specific version, not "latest"

  ---
  8. Docker vs. Alternatives

  Why not just use virtual environments or conda?
  Approach: venv/virtualenv
  Pros: Simple, lightweight, Python-native
  Cons: Only isolates Python packages, not system dependencies or Python version
  ────────────────────────────────────────
  Approach: conda
  Pros: Handles non-Python dependencies, good for data science
  Cons: Large environments, slow package resolution, not truly isolated
  ────────────────────────────────────────
  Approach: Docker
  Pros: Full OS isolation, reproducible across any machine, production-ready
  Cons: Learning curve, slightly more overhead, requires Docker installed
  When to use each:

  - venv: Simple Python projects, all developers use same OS
  - conda: Data science with C/C++ dependencies (CUDA, HDF5)
  - Docker: Multi-dependency apps, deployment to cloud, team collaboration across OSes

  For this project, Docker was the right choice because:
  - Streamlit + Plotly + NBA API have complex dependencies
  - I wanted to deploy to cloud (Linux) while developing on Windows
  - I wanted anyone to run it with one command: docker-compose up

  ---
  9. Lessons Learned

  Docker is worth the learning curve: It took me a few hours to understand images vs. containers, volumes, and
  networking. But once I got it, deployment became trivial.

  Start simple, optimize later: My first Dockerfile was 5 lines. Multi-stage builds and optimizations came after the app
   worked.

  Docker Compose is essential: Manually running docker run with 10 flags is tedious. Compose files are cleaner and
  version-controlled.

  Volumes save you from data loss: Always mount data directories. Learned this the hard way when I lost enriched CSV
  after docker-compose down.

  Docker doesn't replace good architecture: Containers won't fix a poorly designed app. Docker just makes a good app
  easier to deploy.

  ---
  10. Try It Yourself

  Want to run the Wedgie Dashboard locally?

  # Clone the repo
  git clone https://github.com/tommygarner/wedgie-tracker-dashboard.git
  cd wedgie-tracker-dashboard

  # One command to run
  docker-compose up --build

  # Open browser
  http://localhost:8501

  That's it. Docker handles Python version, dependencies, environment setup—everything.

  And if you want to deploy it? Push the image to a registry, spin up a cloud server, and run the same docker-compose up
   command. It will work identically.

  ---
  Tech Stack

  Containerization:
  - Docker 24.x
  - Docker Compose 2.x

  Application:
  - Python 3.11 (in container)
  - Streamlit 1.32+
  - Plotly 5.18+
  - NBA API 1.4+
  - Pandas 2.1+

  Deployment:
  - Local: Docker Compose
  - Cloud: Streamlit Cloud (without Docker) or VPS (with Docker)

  Development:
  - Built with Claude Code for rapid prototyping
  - Version control: Git + GitHub
  - CI/CD: Manual (could add GitHub Actions for auto-builds)

  ---
  If you're building data science applications and haven't tried Docker yet, this project is a great starting point.
  Clone the repo, run docker-compose up, and see how containerization can transform your deployment workflow.

  ---
  Special thanks to Claude Code for building the dashboard features while I focused on the Docker infrastructure. Turns
  out, pairing AI for code and humans for DevOps is a pretty good workflow.

  ---
