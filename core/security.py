# src/vucar/core/security.py
# GPG encryption/decryption functions.
import subprocess
import secrets
import time
from pathlib import Path
from rich.console import Console

console = Console()

def sanitize_and_encrypt_video(source_path: Path, output_path: Path, recipient: str) -> bool:
    """Sanitizes metadata and encrypts video using exiftool | gpg pipe."""
    console.print(f"  -> 🛡️ Sanitizing and Encrypting '{source_path.name}'...")

    exiftool_cmd = [
        "exiftool",
        "-api", "LargeFileSupport=1",  # support files above 4GB but it might a bit unstable. 
        "-all=",           # Wipe all metadata
        "-o", "-",         # Output to stdout
        str(source_path)
    ]

    gpg_cmd = [
        "gpg",
        "--quiet", "--yes", "--batch",
        "--encrypt",       # Asymmetric encryption
        "--recipient", recipient,
        "--output", str(output_path)
    ]

    try:
        # Pipe processes together
        exiftool = subprocess.Popen(exiftool_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gpg = subprocess.Popen(gpg_cmd, stdin=exiftool.stdout, stderr=subprocess.PIPE)
        exiftool.stdout.close()  # Allow exiftool to receive SIGPIPE
        
        # Capture errors while waiting
        _, gpg_err = gpg.communicate()
        exiftool_err = exiftool.stderr.read()

        # Check exit codes
        if exiftool.wait() != 0:
            console.print("[bold red]Error: exiftool failed during sanitization[/bold red]")
            console.print(f"[dim]{exiftool_err.decode('utf-8', 'ignore')}[/dim]")
            return False
            
        if gpg.returncode != 0:
            console.print(f"[bold red]Error: gpg failed (code {gpg.returncode})[/bold red]")
            console.print(f"[dim]{gpg_err.decode('utf-8', 'ignore')}[/dim]")
            return False

        console.print(f"     [green]Created encrypted:[/green] {output_path.name}")
        return True
        
    except FileNotFoundError as e:
        console.print(f"[bold red]Critical: Command missing - {e.filename}[/bold red]")
        return False
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return False

def decrypt_file(encrypted_file_path: Path, decrypted_file_path: Path, user_recipient: str) -> Path | None:
    """
    Decrypts a file using GPG.
    Returns the path to the decrypted file on success, None on failure.
    """
    console.print(f"  ->  Decrypting {encrypted_file_path.name}...")
    try:
        decrypt_cmd = [
            "gpg", "--quiet", "--yes", "--batch",
            "--decrypt",
            "--recipient", user_recipient,
            "--output", str(decrypted_file_path),
            str(encrypted_file_path)
        ]
        subprocess.run(decrypt_cmd, check=True, capture_output=True)
        console.print(f"     [green]Decryption complete. Final file:[/green] {decrypted_file_path}")
        return decrypted_file_path

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Decrypt failed (code {e.returncode}):[/bold red]")
        error_message = e.stderr.decode().strip() if e.stderr else "No error output."
        console.print(f"[dim]{error_message}[/dim]")
        return None
    except FileNotFoundError:
        console.print("[bold red]Error: 'gpg' command not found in PATH.[/bold red]")
        return None
    finally:
        # Clean up the encrypted file after decryption attempt
        encrypted_file_path.unlink(missing_ok=True)
