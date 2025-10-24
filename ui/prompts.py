# vucar/ui/prompts.py

import questionary
from rich.console import Console
console = Console()

def ask_for_final_command(presets: dict) -> str | None:
    """
    Asks the user to choose a preset or custom command, displaying the
    command string in the list, then presents it for final review.

    This uses a two-step process:
    1. Select from a formatted list of presets or a 'Custom' option.
    2. Review and edit the chosen command in a final text input.

    Returns the final command string or None if the user cancels.
    """
    # --- Part 1: Prepare and Display the Selection Prompt ---

    # Find the longest preset name to calculate padding for alignment
    # This ensures all command strings start at the same column
    max_name_len = 0
    if presets:
        max_name_len = max(len(details["name"]) for details in presets.values())

    # Create a list of choices for questionary
    # And a mapping to get the command back from the user's choice
    choices = []
    choice_to_command = {}

    for preset, details in presets.items():
        name = details["name"]
        command = details["command"]
        
        # ljust adds padding to the right of the name for alignment
        display_string = f"{name.ljust(max_name_len + 4)}{command}"
        
        choices.append(display_string)
        choice_to_command[display_string] = command # Map the full string to the command

    choices.append("Custom FFmpeg Command")

    console.print("\n[bold cyan]-- Step 1 of 2: Choose Encoding Command --[/bold cyan]")
    chosen_option = questionary.select(
        "Select a preset (command is shown on the right), or choose 'Custom':",
        choices=choices,
        use_indicator=True,
    ).ask()

    if chosen_option is None:  # User pressed Ctrl+C
        return None

    # --- Part 2: Determine Command and Show Final Editable Input ---

    initial_command_string = ""
    if chosen_option == "Custom FFmpeg Command":
        console.print("\n[dim]Enter your custom FFmpeg command below.[/dim]")
    else:
        # Retrieve the command using the map we created
        initial_command_string = choice_to_command.get(chosen_option, "")

    console.print("\n[bold yellow]-- Step 2 of 2: Review and Finalize Command --[/bold yellow]")
    console.print("[dim]You can edit the command below. Press Enter to proceed.[/dim]")

    final_command = questionary.text(
        "Final FFmpeg command:",
        default=initial_command_string,
        validate=lambda text: True if len(text.strip()) > 0 else "Command cannot be empty."
    ).ask()

    return final_command