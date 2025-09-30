"""Shared Rich help formatter and utilities for dropfix CLI tools"""
import argparse
import re
import sys
from importlib.metadata import version

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console()


def show_version():
    """Display dropfix version in a Rich panel"""
    version_text = f"[bold white]dropfix[/bold white] [dim]{version('dropfix')}[/dim]"
    console.print(Panel(version_text, border_style="green"))
    sys.exit(0)


class RichHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that uses Rich for help output"""

    def __init__(self, *args, title="Help", **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title

    def format_help(self):
        help_text = super().format_help()
        lines = help_text.split('\n')

        # Extract usage and description
        usage_line = ""
        description = ""
        options = []

        in_options = False
        current_option = None

        for line in lines:
            if line.startswith('usage:'):
                usage_line = line
            elif line.strip() and not line.startswith(' ') and not line.startswith('-') and 'options:' not in line.lower():
                description = line
            elif 'options:' in line.lower():
                in_options = True
            elif in_options and line.strip():
                # Check if this is a new option (starts with whitespace + dash at beginning)
                if re.match(r'^\s{1,4}-', line):
                    # This is a new option flag
                    # Try to parse as option line with description on same line
                    # Pattern handles: -h, --help, --flag ARG, --flag {choice1,choice2}, -f, --flag
                    match = re.match(r'(\s*-[^\s]+(?:\s+[^\s,]+)?(?:,\s+-[^\s]+(?:\s+[^\s,]+)?)?)\s{2,}(.+)', line)
                    if match:
                        # Flag with description on same line
                        flag = match.group(1).strip()
                        desc = match.group(2).strip()
                        current_option = [flag, desc]
                        options.append(current_option)
                    else:
                        # Option flag only, description on next line(s)
                        # This handles flags with arguments or choices like: --dirs DIRS [DIRS ...] or --show {all,ignored,not-ignored}
                        match = re.match(r'^\s{1,4}(-[^\s]+(?:\s+[^\s]+)*)', line)
                        if match:
                            flag = match.group(1).strip()
                            current_option = [flag, ""]
                            options.append(current_option)
                elif current_option and re.match(r'^\s{20,}', line):
                    # Continuation line (heavily indented)
                    if current_option[1]:
                        current_option[1] += " " + line.strip()
                    else:
                        current_option[1] = line.strip()

        # Parse usage line to bold "usage:" and dim the rest
        usage_match = re.match(r'(usage:)(.+)', usage_line)
        if usage_match:
            usage_text = Text()
            usage_text.append(usage_match.group(1), style="bold white")
            usage_text.append(usage_match.group(2), style="dim")
        else:
            usage_text = Text(usage_line, style="white")

        desc_text = Text(description, style="cyan")

        # Create table for options
        options_table = Table(show_header=False, box=None, padding=(0, 2), border_style=None)
        options_table.add_column("Flag", style="bright_green", no_wrap=True)
        options_table.add_column("Description", style="dim")

        for flag, desc in options:
            options_table.add_row(flag, desc)

        # Build layout
        help_group = Group(
            usage_text,
            Text(""),
            desc_text,
            Text(""),
            Text("options:", style="bold white"),
            options_table
        )

        # Only print if we have actual options (not being called during parser init)
        if options:
            console.print(Panel(help_group, title=f"[bold cyan]{self.title}[/bold cyan]", border_style="cyan"))
            sys.exit(0)

        # Return empty string for intermediate calls during parser construction
        return ""