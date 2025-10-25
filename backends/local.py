import subprocess
from pathlib import Path
from rich.console import Console
from vucar.backends.base import Backend
import shlex

# --- MODIFICATION START ---
# Import the new builder function
from vucar.core.ffmpeg import build_ffmpeg_command
# --- MODIFICATION END ---

console = Console()

class LocalBackend(Backend):
    """
    Executes video processing tasks on the local machine.
    """
    def execute(self, video_path: Path, command: str) -> bool:
        # 1. Define the output path for the processed file
        output_path = video_path.with_name(f"{video_path.stem}-processed{video_path.suffix}")
        
        # --- REPLACEMENT START ---
        # 2. Delegate command creation to the core utility
        full_command_list = build_ffmpeg_command(
            input_path=video_path,
            output_path=output_path,
            command_options=command
        )
        # --- REPLACEMENT END ---

        # 3. For display purposes, join the list back into a readable string
        display_command = shlex.join(full_command_list)
        
        console.print(f"  -> ⚙️ Executing locally...")
        console.print(f"     [dim]Input: {video_path}[/dim]")
        console.print(f"     [dim]Output: {output_path}[/dim]")
        console.print(f"     [cyan]$ {display_command}[/cyan]")

        try:
            # 4. Execute the command.
            # --- MODIFICATION: ADDED STDERR CAPTURE FOR BETTER DEBUGGING ---
            result = subprocess.run(
                full_command_list, 
                check=True, 
                capture_output=True, 
                text=True
            )
            console.print("     [green]Local execution complete.[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Local execution failed.[/bold red]")
            # Print the actual error from FFmpeg
            console.print("[dim]FFmpeg Error Output:[/dim]")
            console.print(f"[red]{e.stderr}[/red]")
            return False
        except FileNotFoundError:
            console.print("[bold red]Error: 'ffmpeg' command not found. Is FFmpeg installed and in PATH?[/bold red]")
            return False