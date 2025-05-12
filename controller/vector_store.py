import logging
from typing import Tuple, Optional, Any

# Configure the logger
logging.basicConfig(level=logging.INFO)

def initialize_vector_store(api_client: Any, vector_store_name: str) -> Tuple[Optional[Any], bool]:
    """
    Creates or retrieves a vector store by name.

    Parameters:
    - api_client: Client object for interacting with the OpenAI API.
    - vector_store_name: Name of the vector store to create or retrieve.

    Returns:
    - Tuple[Optional[Any], bool]: The created or retrieved vector store object and a boolean indicating 
      whether it was newly already existed (True) or not (False). Returns (None, True) if an error occurs.
    """
    try:
        # Retrieve list of existing vector stores
        vector_stores = api_client.vector_stores.list()
        # Check if a store with the given name already exists
        existing_store = next((store for store in vector_stores if store.name == vector_store_name), None)
        
        if existing_store:
            logging.info(f"Vector store '{vector_store_name}' already exists with ID: {existing_store.id}")
            return existing_store, True

        # Create a new vector store if it doesn't exist
        vector_store = api_client.vector_stores.create(name=vector_store_name)
        logging.info(f"New vector store created with ID: {vector_store.id}")
        return vector_store, False

    except (AttributeError, TypeError, ValueError) as error:
        logging.error(f"Error creating or retrieving vector store: {error}")
        return None, True
