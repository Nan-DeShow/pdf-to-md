import os
import zipfile
from markitdown import MarkItDown

## gets a list of files in the 'files' directory
def get_files_in_directory(directory_path):
  """
  Returns a list of files in the specified directory.

  Args:
    directory_path: The path to the directory.

  Returns:
    A list of file names in the directory.
  """
  try:
    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    return files
  except FileNotFoundError:
    return f"Error: Directory not found: {directory_path}"
  except NotADirectoryError:
    return f"Error: Not a directory: {directory_path}"

## unzips any zip files in the 'files' directory
def unzip_file(zip_filepath, extract_to_path):
    """
    Extracts all files from a ZIP archive.

    Args:
        zip_filepath (str): The path to the ZIP file.
        extract_to_path (str): The directory to extract the contents to. 
                               If None, it will extract to the current directory.
    """
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_to_path)
        print(f"Successfully extracted '{zip_filepath}' to '{extract_to_path}'.")
    except FileNotFoundError:
        print(f"Error: The file '{zip_filepath}' was not found.")
    except zipfile.BadZipFile:
         print(f"Error: The file '{zip_filepath}' is not a valid ZIP file.")

## Converts a PDF file to Markdown format
def convert_to_md (file):
    details = file.split('.')
    name = details[0]
    file_type = details[1]
    product = f"files/{name}"

    if file_type == "zip":
        zip = f"files/{name}.zip"
        extract_to_path = "unzipped_pdfs"

        unzip_file(zip, extract_to_path)
        product = f"./unzipped_pdfs/{name}"

    md = MarkItDown(enable_plugins=False)
    f = open(f"markdown_files/{name}.md", "x")
    result = md.convert(f"{product}.pdf")
    print(result.text_content)
    f.write(result.text_content)
    f.close()

## Main execution
directory_path = "./files"

file_list = get_files_in_directory(directory_path)

if isinstance(file_list, str):
    print(file_list) # Print the error message
else:
    print(f"Files in '{directory_path}':")
    for file_name in file_list:
        print(f"- {file_name}")
        convert_to_md(file_name)