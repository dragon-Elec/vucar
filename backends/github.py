# src/vucar/backends/github.py
# GitHub Actions workflow implementation.
import subprocess
import time
import secrets
import json
from pathlib import Path
from rich.console import Console
from vucar.backends.base import Backend
from vucar.core.video import get_file_size, restore_metadata
from vucar.core.security import sanitize_and_encrypt_video, decrypt_file
import tempfile
import os
import tempfile

console = Console()

# Define the absolute path to the root of the git repository.
# This makes the script runnable from any directory.
# Logic: from github.py -> up to backends/ -> up to vucar/ -> down into config/ -> down into git_context/
GIT_REPO_ROOT = Path(__file__).resolve().parent.parent / "config" / "git_context"


SIZE_THRESHOLD_GIB = 2_147_483_648  # 2 GiB in bytes
SIZE_THRESHOLD_GB = 4_294_967_296  # 4 GB in bytes

class GitHubBackend(Backend):
    """
    Executes video processing tasks using GitHub Actions workflows.
    """
    def __init__(self, repo: str, workflow_file: str, default_branch: str, action_gpg_recipient: str, user_gpg_recipient: str):
        self.repo = repo
        self.workflow_file = workflow_file
        self.default_branch = default_branch
        self.action_gpg_recipient = action_gpg_recipient
        self.user_gpg_recipient = user_gpg_recipient

    def _upload_via_github_release(self, file_path: Path) -> str | None:
        """
        Creates a temporary release and uploads a file as an asset.
        Returns the tag name on success, None on failure.
        """
        tag = f"temp-upload-{secrets.token_hex(8)}"
        console.print(f"  -> ☁️ Uploading via GitHub Release (tag: [bold magenta]{tag}[/bold magenta])...")

        try:
            # Create and push the git tag, specifying the repo path with -C
            subprocess.run(["git", "-C", str(GIT_REPO_ROOT), "tag", tag], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(GIT_REPO_ROOT), "push", "origin", tag], check=True, capture_output=True)
            console.print("     [dim]Pushed git tag.[/dim]")

            # Create the GitHub release
            subprocess.run(
                ["gh", "release", "create", tag, "--repo", self.repo, "--prerelease", "--title", f"Temp Upload {tag}"],
                check=True, capture_output=True
            )
            console.print("     [dim]Created GitHub release.[/dim]")

            # Upload the file as a release asset
            subprocess.run(
                ["gh", "release", "upload", tag, str(file_path), "--repo", self.repo, "--clobber"],
                check=True, capture_output=True
            )
            console.print(f"     [green]Uploaded asset:[/green] {file_path.name}")
            
            return tag

        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]GitHub upload failed (code {e.returncode}):[/bold red]")
            error_message = e.stderr.decode('utf-8', 'ignore').strip()
            console.print(f"[dim]{error_message}[/dim]")
            # Attempt to clean up the failed tag, specifying the repo path with -C
            subprocess.run(["git", "-C", str(GIT_REPO_ROOT), "tag", "-d", tag], capture_output=True)
            subprocess.run(["git", "-C", str(GIT_REPO_ROOT), "push", "--delete", "origin", tag], capture_output=True)
            return None
        except FileNotFoundError as e:
            console.print(f"[bold red]Critical: Command missing - {e.filename}[/bold red]")
            return None

    def _upload_via_tempsh(self, file_path: Path) -> str | None:
        """
        Uploads a file to temp.sh using curl and returns the URL.
        """
        console.print("  -> ☁️ Uploading via temp.sh...")

        cmd = [
            "curl",
            "--progress-bar",
            "-F", f"file=@{file_path}",
            "https://temp.sh/upload"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            upload_url = result.stdout.strip()

            if not upload_url.startswith("http"):
                console.print("[bold red]Error: temp.sh did not return a valid URL.[/bold red]")
                console.print(f"[dim]Received: {upload_url}[/dim]")
                return None

            console.print(f"     [green]Upload complete. URL:[/green] {upload_url}")
            return upload_url

        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]curl failed (code {e.returncode}):[/bold red]")
            error_message = e.stderr.strip()
            console.print(f"[dim]{error_message}[/dim]")
            return None
        except FileNotFoundError:
            console.print("[bold red]Critical: Command 'curl' not found in PATH.[/bold red]")
            return None

    def _trigger_workflow_run(
        self,
        ffmpeg_options_json: str,
        output_filename_base: str,
        release_tag: str | None = None,
        upload_url: str | None = None,
    ) -> bool:
        """
        Triggers the GitHub Actions workflow with the correct parameters.
        """
        console.print("  ->  Triggering GitHub Actions workflow...")

        cmd = [
            "gh", "workflow", "run", self.workflow_file,
            "--repo", self.repo,
            "--ref", self.default_branch,
            "-f", f"ffmpeg_options={ffmpeg_options_json}",
            "-f", f"output_filename_base={output_filename_base}"
        ]

        if release_tag:
            cmd.extend(["-f", f"release_tag={release_tag}"])
        elif upload_url:
            cmd.extend(["-f", f"upload_url={upload_url}"])
        else:
            console.print("[bold red]Error: No upload method provided to trigger workflow.[/bold red]")
            return False

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            console.print("     [green]Workflow triggered successfully.[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Workflow trigger failed (code {e.returncode}):[/bold red]")
            error_message = e.stderr.strip()
            console.print(f"[dim]{error_message}[/dim]")
            return False
        except FileNotFoundError:
            console.print("[bold red]Critical: Command 'gh' not found in PATH.[/bold red]")
            return False

    def _monitor_workflow_run(self) -> str | None:
        """
        Waits for the latest workflow run to complete, retrying on network failure,
        while showing the interactive gh watch output.
        Returns the run ID on success.
        """
        console.print("  -> ⏳ Waiting for workflow to complete... (This may take a while)")
        
        time.sleep(8)

        max_retries, delay = 3, 5
        run_id = None 

        for attempt in range(1, max_retries + 1):
            try:
                if not run_id:
                    run_list_cmd = [
                        "gh", "run", "list", "--workflow", self.workflow_file, "--repo", self.repo,
                        "--limit", "1", "--json", "databaseId,url", "-q", ".[0]"
                    ]
                    latest_run_json_str = subprocess.check_output(run_list_cmd, text=True).strip()
                    
                    if not latest_run_json_str or latest_run_json_str == "null":
                        raise ValueError("Could not retrieve latest workflow run details.")
                    
                    latest_run = json.loads(latest_run_json_str)
                    run_id = str(latest_run['databaseId'])
                    run_url = latest_run['url']
                    
                    console.print(f"     [dim]Monitoring Run ID {run_id}[/dim]")
                    console.print(f"     [dim]URL: {run_url}[/dim]")

                watch_cmd = ["gh", "run", "watch", run_id, "--repo", self.repo, "--exit-status"]
                subprocess.run(watch_cmd, check=True)

                console.print("     [green]Workflow finished.[/green]")
                return run_id

            except (subprocess.CalledProcessError, ValueError) as e:
                if attempt < max_retries:
                    console.print(f"[yellow]Monitoring attempt {attempt} failed. Retrying in {delay}s...[/yellow]")
                    time.sleep(delay)
                    delay *= 2
                else:
                    console.print(f"[bold red]Monitoring failed after {max_retries} attempts.[/bold red]")
                    error_message = e.stderr.decode().strip() if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
                    if error_message:
                        console.print(f"[dim]{error_message}[/dim]")
                    return None
                    
        return None

    def _download_artifact(self, run_id: str, output_filename_base: str) -> Path | None:
        """
        Downloads the output artifact with retries (using exponential backoff).
        Returns the path to the downloaded (encrypted) file on success, None on failure.
        """
        console.print("  ->  Downloading artifact...")

        final_encrypted_file_name = f"{output_filename_base}.gpg"
        # download_dir = Path(tempfile.gettempdir()) # Download to temporary directory
        download_dir = Path.cwd() # Download to current working directory for now

        max_retries, delay = 3, 5

        for attempt in range(1, max_retries + 1):
            try:
                download_cmd = [
                    "gh", "run", "download", run_id, "--repo", self.repo,
                    "--name", output_filename_base, "--dir", str(download_dir)
                ]
                # Ensure the target file doesn't exist before download
                (download_dir / final_encrypted_file_name).unlink(missing_ok=True)
                
                subprocess.run(download_cmd, check=True, capture_output=True, text=True)
                console.print("     [dim]Artifact downloaded successfully.[/dim]")
                return download_dir / final_encrypted_file_name

            except subprocess.CalledProcessError as e:
                if attempt < max_retries:
                    console.print(f"[yellow]Download attempt {attempt} failed. Retrying in {delay}s...[/yellow]")
                    time.sleep(delay)
                    delay *= 2
                else:
                    console.print(f"[bold red]Download failed after {max_retries} attempts.[/bold red]")
                    error_message = e.stderr.strip() or "No error output."
                    console.print(f"[dim]{error_message}[/dim]")
                    return None
            except FileNotFoundError:
                console.print("[bold red]Critical: Command 'gh' not found in PATH.[/bold red]")
                return None
        return None # Should not be reached if successful or max_retries hit

    def _cleanup_github_release(self, tag: str):
        """
        Deletes GitHub release and associated tag with best-effort approach.
        """
        console.print(f"  -> 🧹 Cleaning up GitHub release '{tag}'...")
        
        try:
            subprocess.run(
                ["gh", "release", "delete", tag, "--repo", self.repo, "--yes"],
                check=True, capture_output=True, text=True
            )
            console.print(f"     [dim]Deleted release {tag}[/dim]")
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() or e.stdout.strip()
            console.print(f"[yellow]Release deletion warning: {err}[/yellow]")
        
        try:
            subprocess.run(
                ["git", "-C", str(GIT_REPO_ROOT), "push", "--delete", "origin", tag],
                check=True, capture_output=True, text=True
            )
            console.print(f"     [dim]Deleted tag {tag}[/dim]")
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() or e.stdout.strip()
            console.print(f"[yellow]Tag deletion warning: {err}[/yellow]")

    def execute(self, video_path: Path, command: str) -> Path | None:


        console.print("\n[bold blue] Starting GitHub Actions processing pipeline...[/bold blue]")
        
        output_filename_base = secrets.token_hex(8)
        temp_dir = Path(tempfile.gettempdir())
        encrypted_file_path = temp_dir / f"{output_filename_base}.gpg"
        
        console.print(f"  Job Name: [bold magenta]{output_filename_base}[/bold magenta]")

        release_tag = None
        run_id = None
        try:
            # Phase 1: Sanitize and Encrypt the local file
            success = sanitize_and_encrypt_video(
                source_path=video_path,
                output_path=encrypted_file_path,
                recipient=self.action_gpg_recipient
            )
            if not success:
                return None

            # Phase 2: Analyze Size and Upload
            file_size = get_file_size(encrypted_file_path)
            upload_url = None

            if file_size < SIZE_THRESHOLD_GIB:
                release_tag = self._upload_via_github_release(
                    file_path=encrypted_file_path
                )
            elif file_size < SIZE_THRESHOLD_GB:
                upload_url = self._upload_via_tempsh(file_path=encrypted_file_path)
            else:
                console.print(f"[bold red]Error: File size ({file_size} bytes) exceeds the 4GB limit.[/bold red]")
                return None

            if not release_tag and not upload_url:
                console.print("[bold red]Pipeline halted due to upload failure.[/bold red]")
                return None

            # Phase 3: Trigger Remote Workflow
            ffmpeg_options_json = json.dumps({"command": command})
            
            success = self._trigger_workflow_run(
                ffmpeg_options_json=ffmpeg_options_json,
                output_filename_base=output_filename_base,
                release_tag=release_tag,
                upload_url=upload_url
            )

            if not success:
                console.print("[bold red]Pipeline halted due to workflow trigger failure.[/bold red]")
                return None

            # Phase 4: Monitor Workflow
            run_id = self._monitor_workflow_run()
            
            if not run_id:
                console.print("[bold red]Pipeline halted due to monitoring failure.[/bold red]")
                return None

            # NEW: Download the artifact
            downloaded_encrypted_file_path = self._download_artifact(
                run_id=run_id,
                output_filename_base=output_filename_base
            )

            if not downloaded_encrypted_file_path:
                console.print("[bold red]Pipeline halted due to artifact download failure.[/bold red]")
                return None

            # NEW: Decrypt the downloaded artifact
            decrypted_file_path = decrypt_file(
                encrypted_file_path=downloaded_encrypted_file_path,
                decrypted_file_path=video_path.with_name(f"{video_path.stem}!{video_path.suffix}"), # Use original input path for naming
                user_recipient=self.user_gpg_recipient
            )

            if not decrypted_file_path:
                console.print("[bold red]Pipeline failed during decryption.[/bold red]")
                return None
            
            console.print("  ->  restoring metadata")
            restore_metadata(source_path=video_path, target_path=decrypted_file_path)

            console.print("\n[bold green]✅ Success! Your compressed file is ready.[/bold green]")
            return decrypted_file_path

        except Exception as e:
            console.print(f"[bold red]An error occurred during GitHub Actions execution: {e}[/bold red]")
            return None
        finally:
            # Final Cleanup Phase
            console.print("---")
            if encrypted_file_path.exists():
                encrypted_file_path.unlink()
                console.print(f"     [dim]Deleted temporary encrypted file: {encrypted_file_path.name}[/dim]")
            if release_tag:
                self._cleanup_github_release(tag=release_tag)