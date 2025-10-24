# vucar/backends/local.py
import subprocess
from pathlib import Path
from rich.console import Console
from vucar.backends.base import Backend
import shlex  # For safely splitting and joining command arguments

console = Console()

class LocalBackend(Backend):
    """
    Executes video processing tasks on the local machine.
    """
    def execute(self, video_path: Path, command: str) -> bool:
        # 1. Define the output path for the processed file
        output_path = video_path.with_name(f"{video_path.stem}-processed{video_path.suffix}")
        
        # 2. Construct the full command as a list for security and reliability
        # This is the original behavior you wanted.
        full_command_list = [
            "ffmpeg",
            "-i",
            str(video_path)
        ]
        
        # Add the options from the preset file, splitting them correctly
        full_command_list.extend(shlex.split(command))
        
        # Add the final output file path
        full_command_list.append(str(output_path))

        # 3. For display purposes, join the list back into a readable string
        display_command = shlex.join(full_command_list)
        
        console.print(f"  -> ⚙️ Executing locally...")
        console.print(f"     [dim]Input: {video_path}[/dim]")
        console.print(f"     [dim]Output: {output_path}[/dim]")
        console.print(f"     [cyan]$ {display_command}[/cyan]")

        try:
            # 4. Execute the command. Because it's a list, shell=True is not needed.
            subprocess.run(full_command_list, check=True)
            console.print("     [green]Local execution complete.[/green]")
            return True
        except subprocess.CalledProcessError:
            console.print(f"[bold red]Local execution failed.[/bold red]")
            return False
        except FileNotFoundError:
            console.print("[bold red]Error: 'ffmpeg' command not found. Is FFmpeg installed and in PATH?[/bold red]")
            return False