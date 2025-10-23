# VUCAR: Video Unified Computation & Automation Resource

This project aims to refactor a monolithic video processing toolkit into a modular, backend-driven framework. It allows users to seamlessly execute video processing tasks on different environments, from local machines to remote CI/CD pipelines.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/vucar.git
    cd vucar
    ```

2.  **Install dependencies (using pip):**

    ```bash
    pip install -e .
    ```

    Or using `poetry` (if you set it up):

    ```bash
    poetry install
    poetry shell
    ```

## Usage

To run the video processing toolkit, use the `vucar` command followed by the `run` subcommand and the path to your video file.

```bash
vucar run <path_to_video_file> [OPTIONS]
```

### Options:

*   `--backend, -b`: Specify the backend to use. Options: `local` (default), `github`.
*   `--verbose, -v`: Show raw output for debugging.

### Examples:

**Run locally:**

```bash
vucar run my_video.mp4 --backend local
```

**Run via GitHub Actions:**

```bash
vucar run my_video.mp4 --backend github
```

## Configuration

Create a `config.toml` file in the project root with your GitHub repository details and GPG key information:

```toml
[user]
repo = "your-username/your-repo"
workflow_file = "your_workflow.yml"
default_branch = "main"
action_gpg_recipient = "github-action-gpg-key-id"
user_gpg_recipient = "your-gpg-key-id"
```

Create a `presets.toml` file in the project root for FFmpeg command presets:

```toml
[preset_name_1]
name = "Preset 1 Description"
command = "ffmpeg -i {input} -c:v libx264 -crf 23 {output}"

[preset_name_2]
name = "Preset 2 Description"
command = "ffmpeg -i {input} -c:v libvpx-vp9 -crf 30 {output}"
```

## Project Structure

```
vucar/
├── __main__.py
├── cli.py
├── config.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── vucar blueprint.md
├── backends/
│   ├── __init__.py
│   ├── base.py
│   ├── github.py
│   └── local.py
├── core/
│   ├── __init__.py
│   ├── ffmpeg.py
│   ├── security.py
│   └── video.py
└── ui/
    ├── __init__.py
    └── prompts.py
```
