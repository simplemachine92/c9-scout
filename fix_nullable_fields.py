#!/usr/bin/env python3
"""
Post-processing script to fix nullable fields in ariadne-codegen generated Pydantic models.

This script adds default=None to Optional fields that use Field(alias=...) without a default.
"""

import re
import os
import glob

def fix_nullable_fields(file_path):
    """Fix nullable fields in a generated Python file."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern to match: field_name: Optional[Type] = Field(alias="fieldName")
    # Replace with: field_name: Optional[Type] = Field(default=None, alias="fieldName")
    pattern = r'(\w+): Optional\[([^\]]+)\] = Field\(alias="([^"]+)"\)'

    def replacement(match):
        field_name = match.group(1)
        type_hint = match.group(2)
        alias = match.group(3)
        return f'{field_name}: Optional[{type_hint}] = Field(default=None, alias="{alias}")'

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed nullable fields in {file_path}")
        return True
    return False

def main():
    """Fix all generated client files."""
    client_dir = "clients/central_client"
    if not os.path.exists(client_dir):
        print(f"Directory {client_dir} not found")
        return

    # Find all Python files in the client directory
    python_files = glob.glob(os.path.join(client_dir, "*.py"))

    fixed_count = 0
    for file_path in python_files:
        if fix_nullable_fields(file_path):
            fixed_count += 1

    print(f"Fixed nullable fields in {fixed_count} files")

if __name__ == "__main__":
    main()