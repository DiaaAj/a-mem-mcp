"""Install Claude Code session-start hook for automatic memory usage."""

import os
import shutil
import sys
from pathlib import Path


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
                return True  # Still success - our hook is installed
        except Exception as e:
            print(f"Warning: Could not read existing hook: {e}", file=sys.stderr)
            return True  # Still success - our hook is installed


def main():
    """CLI entry point for manual hook installation."""
    print("Installing A-MEM session-start hook...")
    success = install_hook()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
