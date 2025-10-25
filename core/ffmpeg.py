#!/usr/bin/env python3
# vucar/core/ffmpeg.py
import shlex
from pathlib import Path
from typing import List

def build_ffmpeg_command(
    input_path: Path, 
    output_path: Path, 
    command_options: str
) -> List[str]:
    """
    Safely assembles a full FFmpeg command as a list of arguments.

    This centralizes command creation, ensuring all backends use the
    exact same command structure.

    Args:
        input_path: Path to the source video file.
        output_path: Path for the processed output video.
        command_options: The string of FFmpeg options from the preset (e.g., "-c:v libx265 ...").

    Returns:
        A list of strings representing the full command, ready for subprocess.
    """
    command_list = [
        "ffmpeg",
        "-i",
        str(input_path)
    ]
    
    # Safely split the user-provided options string
    command_list.extend(shlex.split(command_options))
    
    # Add the final output file path
    command_list.append(str(output_path))
    
    return command_list