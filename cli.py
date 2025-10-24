#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the parent directory of 'vucar' to sys.path
# This allows running cli.py directly when it's part of a package
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

import typer
from vucar.backends.local import LocalBackend
from vucar.backends.github import GitHubBackend
from rich.console import Console
from vucar.core.config import load_presets, load_user_config
# MODIFIED: Import the new unified function
from vucar.ui.prompts import ask_for_final_command


app = typer.Typer()
console = Console()

@app.command()
def run(
    video_file: str = typer.Argument(..., help="Path to the video file to process."),
    backend: str = typer.Option("github", "--backend", "-b", help="Backend to use: 'local' or 'github'."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show raw output for debugging.")
):
    """
    Encrypts, uploads, and processes a video file using a remote GitHub Actions workflow.
    """
    try:
        console.print(f"▶️  Starting CI Toolkit for file: [bold cyan]{video_file}[/bold cyan]")
        
        # --- Step 0: Validate Input File ---
        video_path = Path(video_file)
        if not video_path.exists():
            console.print(f"[bold red]Error: The file '{video_file}' does not exist.[/bold red]")
            raise typer.Abort()
        
        # --- Step 1: Load Presets & Config ---
        all_presets = load_presets()
        user_config = load_user_config()
        
        # --- Step 2 & 3 (REPLACED): Get Final Command String ---
        # This new function handles choosing, displaying, and editing the command.
        ffmpeg_command_string = ask_for_final_command(all_presets)
        
        if not ffmpeg_command_string:
            console.print("\n[bold yellow]No command provided. Aborting.[/bold yellow]")
            raise typer.Abort()

        # This is the single, simple payload we will send
        final_payload = {"command": ffmpeg_command_string}
            
        console.print("\n[bold green]Final FFmpeg command to be executed remotely:[/bold green]")
        console.print(f"[cyan]{ffmpeg_command_string}[/cyan]")

        # --- Start the Processing Pipeline ---
        console.print("\n[bold blue] Starting processing pipeline...[/bold blue]")
        
        selected_backend = None
        if backend == "local":
            selected_backend = LocalBackend()
        elif backend == "github":
            selected_backend = GitHubBackend(
                repo=user_config["repo"],
                workflow_file=user_config["workflow_file"],
                default_branch=user_config["default_branch"],
                action_gpg_recipient=user_config["action_gpg_recipient"],
                user_gpg_recipient=user_config["user_gpg_recipient"]
            )
        else:
            console.print(f"[bold red]Error: Unknown backend '{backend}'. Choose 'local' or 'github'.[/bold red]")
            raise typer.Abort()

        if selected_backend.execute(video_path=video_path, command=ffmpeg_command_string):
            console.print("\n[bold green]✅ Processing complete![/bold green]")
        else:
            console.print("\n[bold red]❌ Processing failed.[/bold red]")
            raise typer.Abort()

    except FileNotFoundError as e:
        console.print(f"[bold red]Critical error: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Abort()
    except typer.Abort:
        # Let Typer handle this gracefully for a clean exit.
        # It will print "Aborted!" by default.
        raise
    except Exception:
        console.print(f"[bold red]An unexpected error occurred:[/bold red]")
        # For truly unexpected errors, show the full traceback
        console.print_exception(show_locals=True)
        raise typer.Abort()

if __name__ == "__main__":
    app()