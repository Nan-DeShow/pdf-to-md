import os
import zipfile
from markitdown import MarkItDown

import asyncio
import json
import logging
import sys
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def message_handler(msg):
    global type
    global counter
    subject = msg.subject
    data = msg.data.decode()
    print(f"Received a message on '{subject}': {data}")

    
    if msg.reply:
        await msg.respond(f"Processed message: {data}".encode())
        print(f"Sent reply for message on {subject}")

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
    #print(result.text_content)
    f.write(result.text_content)
    f.close()

    return result.text_content



async def main():
    global type
    print("Starting NATS client application...")
    nc = NATS()
    
    try:
        print("Attempting to connect to NATS server...")
        await nc.connect(
            "nats://192.168.1.207:4222",
            connect_timeout=2,
            max_reconnect_attempts=3,
            reconnect_time_wait=1
        )
        print("Successfully connected to NATS server!")

        print("Subscribing to 'example.topic'...")
        await nc.subscribe("example.topic", cb=message_handler)
        print("Successfully subscribed to 'example.topic'")

        directory_path = "./files"

        file_list = get_files_in_directory(directory_path)

        if isinstance(file_list, str):
            print(file_list) # Print the error message
        else:
            print(f"Files in '{directory_path}':")
            for file_name in file_list:
                print(f"- {file_name}")
                message = convert_to_md(file_name)
                test_message = {"message": message}
                await nc.publish("example.topic", test_message["message"].encode())
                print(f"Published message: {test_message['message']}")
                await asyncio.sleep(1)

            print("test")
            
        print("Finished waiting for messages.")

    except ErrNoServers as e:
        print(f"Could not connect to NATS server: {e}", file=sys.stderr)
        raise
    except ErrConnectionClosed as e:
        print(f"NATS connection closed: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        print(f"Error type: {type(e)}", file=sys.stderr)
        raise
    finally:
        try:
            if nc.is_connected:
                await nc.drain()
            await nc.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Error while closing connection: {e}", file=sys.stderr)

if __name__ == "__main__":
    try:
        print("Starting main...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Main program error: {e}", file=sys.stderr)
        sys.exit(1)