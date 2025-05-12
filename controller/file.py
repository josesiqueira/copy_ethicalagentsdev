import os
import logging
from typing import Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

def upload_pdfs_to_vector_store(api_client: Any, vector_store_id: str, directory_path: str) -> bool:
    """
    Uploads PDF files from a specified directory to OpenAI vector store.

    Parameters:
    - api_client: The api_client object for interacting with OpenAI.
    - vector_store_id: The ID of the vector store to upload files to.
    - directory_path: The local directory path containing PDF files.

    Returns:
    - bool: True if all files were uploaded successfully, False otherwise.
    """
    try:
        # Retrieve all existing files in the vector store
        existing_files = get_all_files_from_vector_store(api_client, vector_store_id)
        existing_file_names = {
            get_file_name_by_id(api_client, file.id): file.id
            for file in existing_files
            if get_file_by_id_from_vector_store(api_client, vector_store_id, file.id)
        }
        
        # Get all PDF files from the directory
        file_paths = [os.path.join(directory_path, file) for file in os.listdir(directory_path) if file.lower().endswith(".pdf")]
        
        # Upload files
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            
            # If a file with the same name exists, delete it first
            if file_name in existing_file_names:
                try:
                    delete_file_by_id(api_client, existing_file_names[file_name])
                    logging.info(f"Deleted existing file: {file_name}")
                except Exception as delete_error:
                    logging.error(f"Error deleting file {file_name}: {delete_error}")

            # Upload the new file
            try:
                with open(file_path, "rb") as file:
                    uploaded_file = api_client.beta.vector_stores.files.upload(vector_store_id=vector_store_id, file=file)
                    logging.info(f"Uploaded file: {file_name} with ID: {uploaded_file.id}")
            except (FileNotFoundError, PermissionError) as file_error:
                logging.error(f"Error reading or uploading file {file_name}: {file_error}")
                continue  # Skip this file and move to the next one
        
        logging.info("All files have been uploaded successfully.")
        return True

    except Exception as e:
        logging.error(f"Error uploading files to vector store: {e}")
        return False

# Helper Functions

def get_all_files_from_vector_store(api_client: Any, vector_store_id: str) -> List[Any]:
    """
    Retrieves all files from the specified vector store.

    Parameters:
    - api_client: The api_client object for interacting with OpenAI.
    - vector_store_id: The ID of the vector store from which files are to be retrieved.

    Returns:
    - List of file objects retrieved from the vector store. Returns an empty list if an error occurs.
    """
    try:
        # Retrieve files from the vector store
        file_list = api_client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

        # Log the number of files retrieved
        file_count = len(file_list.data) if file_list.data else 0
        if file_count > 0:
            logging.info(f"Retrieved {file_count} files from vector store with ID: {vector_store_id}.")
        else:
            logging.info(f"No files found in vector store with ID: {vector_store_id}.")

        # Return the list of files or an empty list if none exist
        return file_list.data or []

    except (ConnectionError, ValueError) as error:
        logging.error(f"Error retrieving files from vector store {vector_store_id}: {error}")
        return []
    
def get_file_name_by_id(api_client: Any, file_id: str) -> Optional[str]:
    """
    Retrieves the file name corresponding to a given file ID.

    Parameters:
    - api_client: The api_client object for interacting with OpenAI.
    - file_id: The ID of the file whose name is to be retrieved.

    Returns:
    - str: The filename if found, None otherwise.
    """
    try:
        # Retrieve the list of files
        files = api_client.files.list()

        # Find the file with the matching ID
        file_name = next((file.filename for file in files.data if file.id == file_id), None)

        if file_name:
            logging.info(f"Retrieved file name: {file_name} for ID: {file_id}.")
        else:
            logging.warning(f"No file found with ID: {file_id}.")
            
        return file_name

    except (AttributeError, ConnectionError) as error:
        logging.error(f"Error retrieving file name with ID {file_id}: {error}")
        return None
    
def get_file_by_id_from_vector_store(api_client: Any, vector_store_id: str, file_id: str) -> Optional[Any]:
    """
    Retrieves a file from a specified vector store using the given file ID.

    Parameters:
    - api_client: The api_client object for interacting with OpenAI.
    - vector_store_id: The ID of the vector store to search within.
    - file_id: The ID of the file to be retrieved.

    Returns:
    - The file object if found, None otherwise.
    """
    try:
        # Retrieve the list of files from the specified vector store
        files = api_client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

        # Use a generator expression to find the matching file by ID
        file = next((file for file in files.data if file.id == file_id), None)

        if file:
            logging.info(f"Retrieved file with ID: {file.id} from vector store with ID: {vector_store_id}.")
        else:
            logging.warning(f"No file found with ID: {file_id} in vector store with ID: {vector_store_id}.")
        
        return file

    except (AttributeError, ConnectionError) as error:
        logging.error(f"Error retrieving file with ID {file_id} from vector store {vector_store_id}: {error}")
        return None
    
def delete_file_by_id(api_client: Any, file_id: str) -> bool:
    """
    Deletes a single file by its ID from the attached vector store.

    Parameters:
    - api_client: The api_client object for interacting with OpenAI.
    - file_id: The ID of the file to be deleted.

    Returns:
    - bool: True if the file was successfully deleted, False otherwise.
    """
    try:
        # Delete the file by ID
        api_client.files.delete(file_id)
        logging.info(f"Deleted file with ID: {file_id}")
        return True

    except (FileNotFoundError, PermissionError) as error:
        logging.error(f"Error deleting file with ID {file_id}: {error}")
        return False

    except Exception as e:
        # Catch-all for any other exceptions
        logging.error(f"Unexpected error while deleting file with ID {file_id}: {e}")
        return False