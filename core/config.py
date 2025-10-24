# config.py
import toml
from pathlib import Path

PRESETS_FILE   = Path(__file__).parent.parent / "config" / "presets.toml"
CONFIG_FILE    = Path(__file__).parent.parent / "config" / "config.toml"  

def load_presets() -> dict:
    if not PRESETS_FILE.exists():
        raise FileNotFoundError(f"{PRESETS_FILE.name} not found!")
    return toml.load(PRESETS_FILE)

def load_user_config() -> dict:
    """Loads the [user] section from config.toml."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"{CONFIG_FILE.name} not found. "
            f"Please create it with your repository and GPG key details."
        )
    
    # Load the whole file into a temporary variable
    full_config = toml.load(CONFIG_FILE)
    
    # Check for the 'user' key and return that specific dictionary
    if 'user' in full_config:
        return full_config['user']
    else:
        # Handle cases where the [user] section might be missing
        raise KeyError(f"The required [user] section was not found in {CONFIG_FILE.name}")
