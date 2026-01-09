"""Install Claude Code session-start hook for automatic memory usage."""

import json
import os
import shutil
import sys
from pathlib import Path


def configure_claude_json():
    """Configure ~/.claude.json to register the session-start hook.

    Returns:
        bool: True if successful or already configured, False on error
    """
    claude_json = Path.home() / ".claude.json"

    # Hook configuration to add
    hook_config = {
        "type": "command",
        "command": "$HOME/.claude/hooks/session-start.sh"
    }

    try:
        # Read existing config or create new one
        if claude_json.exists():
            # Backup existing file
            backup_path = claude_json.with_suffix('.json.backup')
            try:
                shutil.copy2(claude_json, backup_path)
            except Exception:
                pass  # Non-critical if backup fails

            # Parse existing JSON
            try:
                with open(claude_json, 'r') as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {claude_json} contains invalid JSON. Creating backup and reinitializing.", file=sys.stderr)
                shutil.copy2(claude_json, claude_json.with_suffix('.json.invalid'))
                config = {}
        else:
            config = {}

        # Ensure hooks structure exists
        if "hooks" not in config:
            config["hooks"] = {}

        if "SessionStart" not in config["hooks"]:
            config["hooks"]["SessionStart"] = []

        # Check if our hook is already configured
        session_start_hooks = config["hooks"]["SessionStart"]
        for entry in session_start_hooks:
            if "hooks" in entry:
                for hook in entry["hooks"]:
                    if hook.get("command") == hook_config["command"]:
                        print("✓ Hook already configured in ~/.claude.json")
                        return True

        # Add our hook configuration
        session_start_hooks.append({
            "hooks": [hook_config]
        })

        # Write back with pretty printing
        claude_json.parent.mkdir(parents=True, exist_ok=True)
        with open(claude_json, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Configured hook in ~/.claude.json")
        return True

    except Exception as e:
        print(f"Warning: Failed to configure ~/.claude.json: {e}", file=sys.stderr)
        print("You may need to manually add the hook configuration.", file=sys.stderr)
        return False


def install_hook():
    """Install the a-mem session-start hook to ~/.claude/hooks/."""
    # Get the hook source file from package
    package_dir = Path(__file__).parent
    hook_source = package_dir / "session-start.sh"

    if not hook_source.exists():
        print(f"Warning: Hook file not found at {hook_source}", file=sys.stderr)
        return False

    # Target directory
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Our unique hook file
    our_hook = hooks_dir / "a-mem-session-start.sh"
    main_hook = hooks_dir / "session-start.sh"

    # Always install/update our hook
    try:
        shutil.copy2(hook_source, our_hook)
        our_hook.chmod(0o755)
        print(f"✓ A-MEM hook installed: {our_hook}")
    except Exception as e:
        print(f"Error: Failed to install A-MEM hook: {e}", file=sys.stderr)
        return False

    # Handle main session-start.sh
    if not main_hook.exists():
        # Create main hook that sources ours
        try:
            main_hook.write_text(f"""#!/bin/bash
# Claude Code session-start hook
# This file sources all hook modules

# A-MEM: Agentic Memory System
source "$HOME/.claude/hooks/a-mem-session-start.sh"
""")
            main_hook.chmod(0o755)
            print(f"✓ Created main hook: {main_hook}")
            # Configure ~/.claude.json
            configure_claude_json()
            print("\n✅ A-MEM is now active! The memory system will activate in all Claude Code sessions.")
            return True
        except Exception as e:
            print(f"Error: Failed to create main hook: {e}", file=sys.stderr)
            return False
    else:
        # Main hook exists - check if it sources ours
        try:
            content = main_hook.read_text()
            source_line = 'source "$HOME/.claude/hooks/a-mem-session-start.sh"'

            if source_line in content or "a-mem-session-start.sh" in content:
                print(f"✓ Main hook already sources A-MEM")
                # Configure ~/.claude.json
                configure_claude_json()
                print("\n✅ A-MEM is now active! The memory system will activate in all Claude Code sessions.")
                return True
            else:
                # Main hook exists but doesn't source ours
                print("\n⚠️  A custom session-start hook already exists")
                print(f"   Location: {main_hook}")
                print("\nTo enable A-MEM auto-activation, add this line to your hook:")
                print(f'   source "$HOME/.claude/hooks/a-mem-session-start.sh"')
                print("\nOr run this command:")
                print(f'   echo \'source "$HOME/.claude/hooks/a-mem-session-start.sh"\' >> ~/.claude/hooks/session-start.sh')
                # Still try to configure .claude.json
                configure_claude_json()
                return True  # Still success - our hook is installed
        except Exception as e:
            print(f"Warning: Could not read existing hook: {e}", file=sys.stderr)
            # Still try to configure .claude.json
            configure_claude_json()
            return True  # Still success - our hook is installed


def main():
    """CLI entry point for manual hook installation."""
    print("Installing A-MEM session-start hook...")
    success = install_hook()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
