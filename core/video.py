# src/vucar/core/video.py
# Video file analysis (size, metadata).
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def get_file_size(file_path: Path) -> int:
    """Returns file size in bytes."""
    console.print(f"  -> 📦 Getting file size for '{file_path.name}'...")
    size = file_path.stat().st_size
    console.print(f"     [dim]Size is {size} bytes.[/dim]")
    return size

def restore_metadata(source_path: Path, target_path: Path, verbose: bool = False) -> bool:
    """Restores metadata from source to target file."""
    console.print(f"  ->  𓂃🖊 Trying metadata restore to '{target_path.name}'...")
    
    cmd = [
        "exiftool",
        "-q",                # Suppress normal output
        "-all=",             # Wipe existing metadata
        "-tagsfromfile", str(source_path),
        "-all:all", "-unsafe",  # Copy all tags including critical ones
        "-overwrite_original",
        str(target_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if verbose and (result.stdout or result.stderr):
            console.print(f"[dim]exiftool: {result.stdout or result.stderr}[/dim]")
        console.print(f"     [green]Metadata restored[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]exiftool failed (code {e.returncode}):[/bold red]")
        console.print(f"[dim]STDOUT: {e.stdout}\nSTDERR: {e.stderr}[/dim]")
        return False
    except FileNotFoundError:
        console.print("[bold red]Error: 'exiftool' not found in PATH[/bold red]")
        return False