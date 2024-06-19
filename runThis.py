"""
This module provides a script runner for a set of predefined scripts.
"""

import os
import subprocess
import sys

def select_script(scripts):
    """Display script options and return the file of the selected script."""
    for key, value in scripts.items():
        print(f"{key}: {value['name']}")

    while True:
        choice = input("Enter the number of the script to run: ")
        if choice in scripts:
            return scripts[choice]['file']
        print("Invalid choice. Please enter a valid number.")


def run_script(*args, **kwargs):
    """Change directory to script location and run the selected script."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    scripts = {
        '1': {
            'name': 'Email Fix - Reads top 40,000 emails and indexes all '
            'unique email addresses [Takes a long time]',
            'file': 'email_fix.py'
        },
        '2': {
            'name': 'Tag All Emails - Manual Script to apply tags to each of '
            'the unique email addresses so they\'re binned correctly',
            'file': 'tag_all_emails.py'
        },
        '3': {
            'name': 'Generate Filter XMLs - Generates the XML file that can '
            'be uploaded to Gmail to apply the filters',
            'file': 'generate_filter_xmls.py'
        }
    }

    script_to_run = select_script(scripts)
    try:
        subprocess.run(['python', os.path.join(os.getcwd(), script_to_run)],check=False)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run script: {e}")
    except KeyboardInterrupt:
        print("Script runner terminated.")


if __name__ == "__main__":
    run_script(*sys.args, **sys.kwargs)
