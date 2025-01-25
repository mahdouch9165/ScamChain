import os
import sys

def print_python_files_and_structure(directory):
    """
    Recursively walk through 'directory', print the folder structure,
    and print the contents of all .py files found.
    """
    for root, dirs, files in os.walk(directory):
        # Determine the nesting level
        level = root.replace(directory, "").count(os.sep)

        # Print current directory name
        indent = "    " * level
        print(f"{indent}{os.path.basename(root)}/")

        # For each .py file in the current directory
        for filename in sorted(files):
            file_indent = "    " * (level + 1)
            print(f"{file_indent}{filename}")

            # Print the contents of the file
            file_path = os.path.join(root, filename)
            with open(file_path, "r", encoding="utf-8", errors='replace') as f:
                file_contents = f.read()

            # Print each line of the file with additional indentation
            content_lines = file_contents.splitlines()
            for line in content_lines:
                print(f"{file_indent}    {line}")


if __name__ == "__main__":
    # Example usage:
    directory_to_explore = "."

    # Open 'code_base.txt' in write mode
    with open("code_base.txt", "w", encoding="utf-8") as outfile:
        # Save a reference to the original stdout
        original_stdout = sys.stdout

        try:
            # Redirect stdout to the file
            sys.stdout = outfile
            # Call the function that does all the printing
            print_python_files_and_structure(directory_to_explore)
        finally:
            # Restore original stdout
            sys.stdout = original_stdout
