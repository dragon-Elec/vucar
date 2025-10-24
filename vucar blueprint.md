## **Project Blueprint Template: `vucar`** 
**V**ideo **U**nified **C**omputation & **A**utomation **R**esource

### 🏛️ **1. Project Overview & Core Mission**

*   **Problem Statement:** (What specific problem is this project trying to solve? Who is it for?)
    > The current video processing toolkit is a monolithic script tightly coupled to a single, complex workflow (GitHub Actions). This makes it inflexible for different use cases, such as quick, local processing on low-power devices (SBCs, Termux), and makes adding new execution methods (e.g., via SSH) difficult and risky.

*   **Mission Statement:** (A concise, one-sentence summary of the project's purpose and goal.)
    > To refactor the toolkit into a modular, backend-driven framework that allows users to seamlessly execute video processing tasks on different environments, from local machines to remote CI/CD pipelines.

*   **Key Objectives / Success Criteria (End State):** (A short, bulleted list of what a "finished" project looks like.)
    1.  [COMPLETED] A `core` library exists, containing all shared, reusable logic (GPG, FFmpeg command generation, video analysis) completely decoupled from any execution environment.
    2.  [COMPLETED] At least two "Execution Backends" are functional: `local` (for SBCs/Termux) and `github` (for the existing CI workflow). But for the current refactors main purpose is to focous on github ci/cd pipeline.
    3.  [COMPLETED] A single, unified Command-Line Interface (`cli.py`) can intelligently select and delegate tasks to the appropriate backend.
    4.  [COMPLETED] The codebase is modular, making the addition of a third backend (e.g., `ssh`) a straightforward and isolated task.

### 🧭 **2. Guiding Principles & Design Philosophy**

(The core values that will guide technical decisions throughout the project.)

*   **Clear Separation of Concerns:** The user-facing CLI (`cli.py`) is a controller. The Execution Backends (`backends/`) are engines. The Core Tools (`core/`) are a shared toolbox. No module will perform the job of another.
*   **Pluggable, Backend-Oriented Architecture:** The application will interact with a generic `Backend` interface. This ensures that the controller can use any backend without knowing its internal implementation details, making them truly swappable.
*   **Pragmatic Modularity:** Code will be organized into modules based on clear, distinct responsibilities. Abstractions will only be created to support the backend-driven design, avoiding unnecessary complexity.
*   **CLI-First User Experience:** The primary interface is the command line. It must be powerful, intuitive, and provide clear feedback. All user interaction logic will be centralized in the `ui` module.
*   **Stateless Execution:** Each backend task will be treated as a self-contained, stateless job. This enhances reliability and predictability, as no run will depend on the state left by a previous one.

### 🏗️ **3. Core Architecture & Project Structure**

(A high-level overview of the architecture and a proposed file/directory structure.)

#### **Architectural Model:**

This project will follow a **3-Layer (Application-Service-Core)** architecture to ensure maintainability and scalability. The layers are:
1.  **The Core/Toolbox Layer (`vucar/core/`):** Standalone, reusable functions for specific tasks (GPG, video analysis). It is completely unaware of where or how it will be used.
2.  **The Service/Backend Layer (`vucar/backends/`):** This layer provides the actual execution services. It uses tools from the Core layer to implement a specific workflow (e.g., the `GitHubBackend` orchestrates encryption, uploading, and monitoring).
3.  **The Application/Presentation Layer (`vucar/cli.py` & `vucar/ui/`):** The user-facing CLI. It captures user intent and delegates the job to the appropriate service backend.

#### **Proposed Directory Structure:**

```
vucar/
├── pyproject.toml              # Project dependencies, metadata, and configuration (single source of truth)
├── README.md
├── vucar blueprint.md
├── __main__.py                 # Main entry point for `python -m vucar`. A thin wrapper that calls the CLI.
├── cli.py                      # Layer 3: The Application Controller (Typer CLI)
│
├── config/               # Configuration files
│   ├── config.toml       # User-specific configuration
│   ├── presets.toml      # FFmpeg command presets
│   └── git_context/      # Isolated git environment for remote operations
│
├── core/                 # Layer 1: The Core Toolbox (Shared Logic)
│   ├── __init__.py
│   ├── config.py         # Configuration loading and validation
│   ├── ffmpeg.py         # FFmpeg command building, splitting logic ("swiss knife")
│   ├── security.py       # GPG encryption/decryption functions
│   └── video.py          # Video file analysis (size, metadata)
│
├── backends/             # Layer 2: The Execution Engines (Backends)
│   ├── __init__.py
│   ├── base.py           # Defines the abstract "Backend" interface contract
│   ├── github.py         # The GitHub Actions workflow implementation
│   └── local.py          # The local machine execution implementation
│
└── ui/                   # Layer 3: User Interaction Components
    ├── __init__.py
    └── prompts.py        # Interactive prompts using questionary
```

### 🧩 **4. Component Breakdown**

(A more detailed look at the key modules from the structure above.)

*   **`core/` (The Toolbox):**
    *   **`ffmpeg.py`:** Will contain functions to build and validate FFmpeg command strings. This is where the future "lossless cutting" logic for large files will be implemented.
    *   **`security.py`:** Contains generic, reusable functions for GPG encryption (`sanitize_and_encrypt_video`) and decryption (`decrypt_file`). It is a core utility and does not contain any backend-specific logic.
    *   **`video.py`:** Will contain functions like `get_file_size` and `restore_metadata` that use tools like `exiftool`.

*   **`backends/` (The Engines):**
    *   **`base.py`:** Will define an Abstract Base Class `Backend` with a method signature like `execute(video_path: Path, command: str)`. All other backends *must* inherit from this and implement this method.
    *   **`github.py`:** Will contain a `GitHubBackend` class. It handles all backend-specific logic for the GitHub Actions workflow, including uploading files, triggering and monitoring the run, and downloading the resulting artifact using the `gh` CLI.
    *   **`local.py`:** Will contain a `LocalBackend` class. Its `execute` method will be very simple: it will just run the provided FFmpeg command as a local subprocess.
    *   **`ssh.py` (Future):** Will contain an `SshBackend` class. It will manage connecting to a remote server, transferring files via SFTP, executing the command remotely, and downloading the result. It will rely on a library like `paramiko`.

*   **`cli.py` (The Controller):**
    *   This is the main Typer application. It will have a command like `run` that accepts a `--backend` option. Based on this option, it will instantiate either `GitHubBackend` or `LocalBackend` and then call its `.execute()` method, passing along the user's inputs.

### 🚀 **5. Phased Development Plan**

(Documenting the project's development through its completed and ongoing phases.)

*   **Phase 1: Minimum Viable Refactor (MVR)** (Completed)
    *   **Goal:** Achieved existing functionality with the new, modular architecture.
    *   **Features:**
        1.  Implemented the `core` library by migrating existing helper functions (`get_file_size`, `encrypt`, etc.).
        2.  Implemented the `LocalBackend` first; it is the simplest and easiest to test.
        3.  Implemented the `GitHubBackend` by migrating the remaining logic from `pipeline.py`.
        4.  Built the new `cli.py` controller that can select and run either backend.

*   **Phase 2: Core Feature Expansion**
    *   **Goal:** Add the "swiss knife" lossless cutting feature and improve robustness.
    *   **Features:**
        1.  Implement the file size check and command-splitting logic in `core/ffmpeg.py`.
        2.  Integrate this new logic into the `base.py` contract so both `LocalBackend` and `GitHubBackend` can use it.
        3.  Refine the configuration system in `core/config.py` to support backend-specific settings.

*   **Phase 3: Remote Execution via SSH**
    *   **Goal:** Enable processing on a user-defined remote server without relying on GitHub.
    *   **Features:**
        1.  Add `paramiko` or a similar library as a project dependency.
        2.  Implement the `SshBackend` class in `backends/ssh.py`.
        3.  Add a `[backend.ssh]` section to `config.toml` for connection parameters (host, user, key_filename).
        4.  Update `cli.py` to recognize and instantiate the `SshBackend`.

*   **Beyond: Long-Term Vision**
    *   Full Termux compatibility and testing.
    *   A plugin system for user-contributed backends or processing steps.

### 📈 **6. Development & Execution Plan**

(The step-by-step process followed during development. These steps have been largely executed during the refactoring phase.)

1.  **Setup:** Created the new directory structure. Initialized a Git repository. Set up a `venv` and a `pyproject.toml` (using a tool like Poetry or Flit is recommended).
2.  **Build the Core Toolbox First:** Isolated the pure helper functions from the old project and moved them into the `core/` modules. Wrote simple, standalone test scripts for each function (e.g., a `test_encrypt.py`) to prove they work in isolation.
3.  **Build the Simplest Backend:** Implemented the `LocalBackend`. Wrote a test script that directly imports and runs `LocalBackend().execute()` to confirm it can process a video on the machine.
4.  **Build the Application Controller:** Created the `cli.py` Typer application. Wired it up to *only* use the `LocalBackend` for now. Tested the end-to-end flow for a local job.
5.  **Integrate the Complex Backend:** Moved the GitHub Actions logic into the `GitHubBackend`. Updated `cli.py` to allow selecting between the local and GitHub backends.
6.  **Test, Refactor, Repeat:** Thoroughly test both end-to-end workflows. Refactor to remove any duplicated code and ensure adherence to the design principles.

### ⚠️ **7. Potential Challenges & Risk Assessment**

(Thinking ahead about what could go wrong.)

*   **Technical Risks:**
    *   The FFmpeg logic for lossless cutting (`-c copy`) can be complex and codec-dependent; it will require careful implementation and testing.
    *   Termux environment might have different binary paths or permissions, requiring platform-specific checks.
    *   Robust subprocess management (handling errors, streaming output) for the `LocalBackend` needs to be carefully designed to provide good user feedback.
    *   **SSH Credential Management:** The `SshBackend` will need secure access to private keys or credentials. The implementation must avoid storing secrets in plain text and should rely on standard methods like SSH agents or encrypted key files with passphrases.

*   **Logistical Risks:**
    *   Refactoring is a significant undertaking. There is a risk of getting bogged down mid-way if the phased plan is not followed.
    *   As a solo project, time is the primary constraint. Sticking to the MVP scope for Phase 1 is critical to avoid burnout.
