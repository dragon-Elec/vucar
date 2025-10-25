# **Project Blueprint: `vucar`**
**V**ideo **U**nified **C**omputation & **A**utomation **R**esource

*Document Version: 2.0 (Post-Refactor)*
*Last Updated: 2025*

---

### 🏛️ **1. Project Overview & Core Mission**

*   **Problem Statement:** Processing large video files is computationally expensive and time-consuming. Users often need to choose between tying up their local machine for hours or navigating complex cloud/CI setups. There is a need for a unified tool that can manage and delegate these heavy tasks to the most appropriate environment, whether it's the local machine or a powerful remote executor.

*   **Mission Statement:** To provide a flexible, backend-driven framework that allows users to seamlessly execute video processing tasks on different environments, from local machines to remote CI/CD pipelines, through a single, intuitive command-line interface.

*   **Key Features:**
    1.  **Dual Execution Backends:** Supports both local (`ffmpeg` on the user's machine) and remote (`GitHub Actions`) processing.
    2.  **Unified CLI:** A single, powerful command (`vucar run`) controls all operations, regardless of the chosen backend.
    3.  **Secure Remote Workflow:** Implements an end-to-end GPG encryption pipeline for the GitHub backend, ensuring video content is never exposed in the remote environment.
    4.  **Extensible Architecture:** Designed from the ground up to easily accommodate new backends (e.g., SSH, other CI services) with minimal effort.
    5.  **User-Friendly Interaction:** Uses clear, interactive prompts to guide users through selecting presets and finalizing commands.

### 🧭 **2. Guiding Principles & Design Philosophy**

*   **Clear Separation of Concerns:** The application is divided into three distinct layers: a user-facing CLI controller (`cli.py`, `ui/`), swappable execution "engines" (`backends/`), and a shared toolbox of utilities (`core/`). No module performs the job of another.
*   **Pluggable, Backend-Oriented Architecture:** The application interacts with a generic `Backend` interface. This ensures the controller can use any backend without knowing its internal implementation, making them truly swappable.
*   **Pragmatic Modularity:** Code is organized into modules based on clear, distinct responsibilities. Abstractions exist solely to support the backend-driven design, avoiding unnecessary complexity.
*   **CLI-First User Experience:** The primary interface is the command line. It is designed to be powerful, intuitive, and provide clear, color-coded feedback for all operations.
*   **Stateless Execution:** Each backend task is treated as a self-contained, stateless job. This enhances reliability and predictability, as no run depends on the state left by a previous one.

### 🏗️ **3. Core Architecture & Project Structure**

#### **Architectural Model:**

This project follows a **3-Layer (Application-Service-Core)** architecture:
1.  **The Core/Toolbox Layer (`vucar/core/`):** Standalone, reusable functions for specific tasks (GPG, video analysis, FFmpeg command building). It is completely unaware of where or how it will be used.
2.  **The Service/Backend Layer (`vucar/backends/`):** Provides the actual execution services. It uses tools from the Core layer to implement a specific workflow (e.g., the `GitHubBackend` orchestrates encryption, uploading, and monitoring).
3.  **The Application/Presentation Layer (`cli.py` & `vucar/ui/`):** The user-facing CLI. It captures user intent and delegates the job to the appropriate service backend.

#### **Directory Structure:**

```
vucar/
├── pyproject.toml              # Project dependencies and metadata
├── README.md
├── vucar blueprint.md
├── cli.py                      # Layer 3: The Application Controller (Typer CLI)
├── __main__.py                 # Allows running the module via `python -m vucar`
│
├── config/
│   ├── config.toml             # User-specific configuration (repo, GPG keys)
│   └── presets.toml            # FFmpeg command presets
│
├── core/                       # Layer 1: The Core Toolbox (Shared Logic)
│   ├── config.py               # Configuration loading functions
│   ├── ffmpeg.py               # FFmpeg command building and validation
│   ├── security.py             # GPG encryption/decryption functions
│   └── video.py                # Video file analysis (size, metadata)
│
├── backends/                   # Layer 2: The Execution Engines (Backends)
│   ├── base.py                 # Defines the abstract "Backend" interface contract
│   ├── github.py               # The GitHub Actions workflow implementation
│   └── local.py                # The local machine execution implementation
│
└── ui/                         # Layer 3: User Interaction Components
    └── prompts.py              # Interactive prompts using `questionary`
```

### 🚀 **4. Phased Development Plan & Roadmap**

*   **Phase 1: Foundation & Refinement (Active)**
    *   **Goal:** Solidify the core architecture and improve robustness.
    *   **Tasks:**
        1.  **Enhance FFmpeg Core:** Expand `core/ffmpeg.py` to include advanced logic, such as command validation and intelligent splitting for large files (lossless cutting).
        2.  **Improve Error Reporting:** Ensure all backends capture and display `stderr` on failure for easier debugging.
        3.  **Configuration Validation:** Implement robust checking in `core/config.py` to provide clear errors for missing or malformed user configs.

*   **Phase 2: Remote Execution via SSH (Next)**
    *   **Goal:** Enable processing on a user-defined remote server without relying on GitHub Actions.
    *   **Tasks:**
        1.  Implement a new `SshBackend` in `backends/ssh.py` using a library like `paramiko`.
        2.  The backend will manage SFTP file transfers, remote command execution, and result retrieval.
        3.  Add a `[backend.ssh]` section to `config.toml` for connection parameters (host, user, key_filename).

*   **Phase 3: Advanced Features & Usability (Future)**
    *   **Goal:** Expand `vucar`'s capabilities and make it more accessible.
    *   **Potential Features:**
        1.  **Termux Compatibility:** Test and adjust for full compatibility with the Termux environment on Android.
        2.  **Plugin System:** Design a system for user-contributed backends or pre/post-processing steps.
        3.  **Configuration Wizard:** Create a `vucar setup` command to interactively generate the initial `config.toml`.

### ⚠️ **5. Potential Challenges & Risk Assessment**

*   **FFmpeg Complexity:** Advanced FFmpeg features like filter graphs or lossless cutting can be codec-dependent and require careful implementation and extensive testing.
*   **SSH Credential Management:** The `SshBackend` will require secure access to private keys or credentials. The implementation must avoid storing secrets in plain text and should rely on standard methods like SSH agents.
*   **Environment Differences:** Ensuring consistent behavior across different environments (Linux desktop, Termux, macOS) may require platform-specific checks for binary paths or permissions.