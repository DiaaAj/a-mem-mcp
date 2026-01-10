"""Install Claude Code session-start hook for automatic memory usage."""

import json
import shutil
import sys
from pathlib import Path

# Paths
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
HOOKS_DIR = Path.home() / ".claude" / "hooks"
MAIN_HOOK = HOOKS_DIR / "session-start.sh"
AMEM_HOOK = HOOKS_DIR / "a-mem-session-start.sh"
HOOK_COMMAND = "$HOME/.claude/hooks/session-start.sh"
SOURCE_LINE = 'source "$HOME/.claude/hooks/a-mem-session-start.sh"'


def configure_claude_settings():
    """Configure ~/.claude/settings.json to register the session-start hook.

    Returns:
        bool: True if successful or already configured, False on error
    """
    hook_config = {
        "type": "command",
        "command": HOOK_COMMAND
    }

    try:
        # Ensure directory exists
        CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)

        # Read existing config or create new one
        if CLAUDE_SETTINGS.exists():
            # Backup existing file
            backup_path = CLAUDE_SETTINGS.with_suffix('.json.backup')
            try:
                shutil.copy2(CLAUDE_SETTINGS, backup_path)
            except Exception:
                pass  # Non-critical if backup fails

            # Parse existing JSON
            try:
                with open(CLAUDE_SETTINGS, 'r') as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {CLAUDE_SETTINGS} contains invalid JSON. Creating backup and reinitializing.", file=sys.stderr)
                shutil.copy2(CLAUDE_SETTINGS, CLAUDE_SETTINGS.with_suffix('.json.invalid'))
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
                        print("✓ Hook already configured in ~/.claude/settings.json")
                        return True

        # Add our hook configuration
        session_start_hooks.append({
            "hooks": [hook_config]
        })

        # Write back with pretty printing
        with open(CLAUDE_SETTINGS, 'w') as f:
            json.dump(config, f, indent=2)

        print("✓ Configured hook in ~/.claude/settings.json")
        return True

    except Exception as e:
        print(f"Warning: Failed to configure ~/.claude/settings.json: {e}", file=sys.stderr)
        print("You may need to manually add the hook configuration.", file=sys.stderr)
        return False


def unconfigure_claude_settings():
    """Remove hook configuration from ~/.claude/settings.json.

    Returns:
        bool: True if successful or already removed, False on error
    """
    if not CLAUDE_SETTINGS.exists():
        print("✓ No ~/.claude/settings.json to clean up")
        return True

    try:
        with open(CLAUDE_SETTINGS, 'r') as f:
            config = json.load(f)

        # Find and remove our hook
        if "hooks" in config and "SessionStart" in config["hooks"]:
            session_start_hooks = config["hooks"]["SessionStart"]
            new_hooks = []

            for entry in session_start_hooks:
                if "hooks" in entry:
                    # Filter out our hook command
                    filtered = [h for h in entry["hooks"] if h.get("command") != HOOK_COMMAND]
                    if filtered:
                        entry["hooks"] = filtered
                        new_hooks.append(entry)
                else:
                    new_hooks.append(entry)

            config["hooks"]["SessionStart"] = new_hooks

            # Clean up empty structures
            if not config["hooks"]["SessionStart"]:
                del config["hooks"]["SessionStart"]
            if not config["hooks"]:
                del config["hooks"]

        # Write back
        with open(CLAUDE_SETTINGS, 'w') as f:
            json.dump(config, f, indent=2)

        print("✓ Removed hook from ~/.claude/settings.json")
        return True

    except Exception as e:
        print(f"Warning: Failed to update ~/.claude/settings.json: {e}", file=sys.stderr)
        return False


def install_hook():
    """Install the a-mem session-start hook to ~/.claude/hooks/."""
    # Get the hook source file from package
    package_dir = Path(__file__).parent
    hook_source = package_dir / "session-start.sh"

    if not hook_source.exists():
        print(f"Warning: Hook file not found at {hook_source}", file=sys.stderr)
        return False

    # Ensure hooks directory exists
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    # Always install/update our hook
    try:
        shutil.copy2(hook_source, AMEM_HOOK)
        AMEM_HOOK.chmod(0o755)
        print(f"✓ A-MEM hook installed: {AMEM_HOOK}")
    except Exception as e:
        print(f"Error: Failed to install A-MEM hook: {e}", file=sys.stderr)
        return False

    # Handle main session-start.sh (resilient wrapper)
    if not MAIN_HOOK.exists():
        # Create main hook that sources ours (with resilience check)
        try:
            MAIN_HOOK.write_text(f"""#!/bin/bash
# Claude Code session-start hook
# This file sources all hook modules (with resilience to missing files)

# A-MEM: Agentic Memory System
if [ -f "$HOME/.claude/hooks/a-mem-session-start.sh" ]; then
    source "$HOME/.claude/hooks/a-mem-session-start.sh"
fi
""")
            MAIN_HOOK.chmod(0o755)
            print(f"✓ Created main hook: {MAIN_HOOK}")
            configure_claude_settings()
            print("\n✅ A-MEM is now active! The memory system will activate in all Claude Code sessions.")
            return True
        except Exception as e:
            print(f"Error: Failed to create main hook: {e}", file=sys.stderr)
            return False
    else:
        # Main hook exists - check if it sources ours
        try:
            content = MAIN_HOOK.read_text()

            if SOURCE_LINE in content or "a-mem-session-start.sh" in content:
                print("✓ Main hook already sources A-MEM")
                configure_claude_settings()
                print("\n✅ A-MEM is now active! The memory system will activate in all Claude Code sessions.")
                return True
            else:
                # Main hook exists but doesn't source ours - append with resilience
                print("⚠️  Existing session-start hook found, appending A-MEM...")
                try:
                    with open(MAIN_HOOK, 'a') as f:
                        f.write(f"""
# A-MEM: Agentic Memory System (added by a-mem install-hook)
if [ -f "$HOME/.claude/hooks/a-mem-session-start.sh" ]; then
    source "$HOME/.claude/hooks/a-mem-session-start.sh"
fi
""")
                    print("✓ Appended A-MEM to existing hook")
                    configure_claude_settings()
                    print("\n✅ A-MEM is now active! The memory system will activate in all Claude Code sessions.")
                    return True
                except Exception as e:
                    print(f"Warning: Could not append to existing hook: {e}", file=sys.stderr)
                    print("\nTo enable A-MEM auto-activation, add this line to your hook:")
                    print(f'   {SOURCE_LINE}')
                    configure_claude_settings()
                    return True  # Still success - our hook file is installed
        except Exception as e:
            print(f"Warning: Could not read existing hook: {e}", file=sys.stderr)
            configure_claude_settings()
            return True  # Still success - our hook is installed


def uninstall_hook():
    """Uninstall the a-mem session-start hook."""
    success = True

    # Remove our hook file
    if AMEM_HOOK.exists():
        try:
            AMEM_HOOK.unlink()
            print(f"✓ Removed {AMEM_HOOK}")
        except Exception as e:
            print(f"Warning: Failed to remove {AMEM_HOOK}: {e}", file=sys.stderr)
            success = False
    else:
        print("✓ A-MEM hook file already removed")

    # Remove source line from main hook (if we added it)
    if MAIN_HOOK.exists():
        try:
            content = MAIN_HOOK.read_text()

            # Check if this is our auto-generated hook (only sources a-mem)
            lines = [l for l in content.strip().split('\n') if l.strip() and not l.strip().startswith('#')]
            is_amem_only = all('a-mem-session-start.sh' in l or l.startswith('if ') or l in ('fi', 'then') for l in lines)

            if is_amem_only:
                # We created this hook - safe to remove entirely
                MAIN_HOOK.unlink()
                print(f"✓ Removed {MAIN_HOOK}")
            elif 'a-mem-session-start.sh' in content:
                # Remove our lines but keep the rest
                new_lines = []
                skip_until_fi = False
                for line in content.split('\n'):
                    if 'A-MEM: Agentic Memory System' in line:
                        skip_until_fi = True
                        continue
                    if skip_until_fi:
                        if line.strip() == 'fi':
                            skip_until_fi = False
                        continue
                    if 'a-mem-session-start.sh' not in line:
                        new_lines.append(line)

                MAIN_HOOK.write_text('\n'.join(new_lines))
                print(f"✓ Removed A-MEM from {MAIN_HOOK}")
            else:
                print("✓ Main hook doesn't reference A-MEM")
        except Exception as e:
            print(f"Warning: Could not update main hook: {e}", file=sys.stderr)
            success = False

    # Remove from settings.json
    unconfigure_claude_settings()

    if success:
        print("\n✅ A-MEM hooks uninstalled successfully.")
    else:
        print("\n⚠️  Uninstall completed with warnings.")

    return success


def main():
    """CLI entry point for manual hook installation."""
    print("Installing A-MEM session-start hook...")
    success = install_hook()
    sys.exit(0 if success else 1)


def main_uninstall():
    """CLI entry point for hook uninstallation."""
    print("Uninstalling A-MEM session-start hook...")
    success = uninstall_hook()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
