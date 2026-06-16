"""
Script to package the application and its dependencies into a ZIP artifact.
Builds the load-balanced-app.zip archive containing app, packages, deploy, and requirements.
"""

from __future__ import annotations

import os
import zipfile

# Define directories and files to include in the deployment bundle
INCLUDES = ["app", "packages", "deploy", "requirements.txt"]
OUTPUT_FILENAME = "load-balanced-app.zip"


def main() -> None:
    """Creates a zip archive with all necessary files for deployment."""
    print(f"Building artifact '{OUTPUT_FILENAME}'...")

    # Open the zip file for writing
    with zipfile.ZipFile(OUTPUT_FILENAME, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in INCLUDES:
            if not os.path.exists(item):
                print(f"Warning: {item} does not exist. Skipping.")
                continue

            if os.path.isdir(item):
                # Recursively add directory contents to the archive
                for root, _, files in os.walk(item):
                    for file in files:
                        # Skip virtual environments or compiled files if present
                        if "__pycache__" in root or file.endswith(".pyc"):
                            continue
                        file_path = os.path.join(root, file)
                        # Archive path preserves directory structure
                        archive_path = os.path.relpath(file_path, start=".")
                        zip_file.write(file_path, archive_path)
                        print(f"Added: {archive_path}")
            else:
                # Add single files directly
                zip_file.write(item, item)
                print(f"Added: {item}")

    print(f"Build complete. Artifact created at: {os.path.abspath(OUTPUT_FILENAME)}")


if __name__ == "__main__":
    main()
