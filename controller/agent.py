import logging
from typing import Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_agent(client: Any, agent_name: str, agent_role: str, model: str, vector_store_id: Optional[str] = None) -> Optional[Any]:
    """
    Creates or retrieves an assistant agent with the given specifications.

    Parameters:
    - client: The API client object for interacting with the OpenAI service.
    - agent_name: The name of the agent to be created or retrieved.
    - agent_role: Instructions or role description for the agent.
    - model: The model to be used for the agent (e.g., gpt-4).
    - vector_store_id: Optional ID of the vector store for file search integration.

    Returns:
    - The created or existing assistant object if successful, None otherwise.
    """
    try:
        # Retrieve the list of existing assistants
        assistants = client.beta.assistants.list()

        # Check if the agent already exists
        for assistant in assistants.data:
            if assistant.name == agent_name:
                if "ai ethicist" in assistant.name.lower():
                    logging.info(f"Found AI Ethicist with ID: {assistant.id}. Returning without changes.")
                    return assistant
                if "riskguard" in assistant.name.lower():
                    logging.info(f"Found RiskGuard with ID: {assistant.id}. Returning without changes.")
                    return assistant
                else:
                    logging.info(f"Agent '{assistant.name}' already exists with ID: {assistant.id}")
                    logging.info(f"Deleting existing Agent '{assistant.name}' with ID: {assistant.id}")
                    delete_agent_by_id(client, assistant.id)
        
        GENERAL_INSTRUCTIONS = """
            You are an expert agent with deep expertise in your assigned domain. Your primary responsibility is to perform tasks and provide responses that align with the **best practices** and methodologies outlined in the documents provided: European Union’s AI Act, Charter of Fundamental Rights of the European Union, European Declaration on Digital Rights and Principles, and the ethical principles outlined by the AI HLEG (High-Level Expert Group on AI). 
            Your responses should be rooted in evidence, referencing the context and specific sections of the documents as needed to ensure accuracy and reliability.

            ### Conversation Structure:
            Your interactions must follow this structured format:
            1. **Reply**: Start by addressing the query or task succinctly, providing a high-level response that sets the context for your analysis.
            2. **Reflection**: Reflect on the provided data, context, or task. Analyze the information deeply, considering all relevant aspects, and justify your reasoning with references to the provided documents or best practices.
            3. **Code/Output**: If applicable, provide code examples, structured outputs, or specific action items that illustrate your recommendations or solutions.
            4. **Critique**: Offer constructive feedback, identifying potential issues, risks, or areas for improvement. Be precise and actionable in your suggestions, ensuring they align with the provided guidelines.

            ### Guidelines for Response:
            - **Alignment with Provided Documents**: Your responses must align with the principles, frameworks, or best practices outlined in the provided documents. For instance:
            - Reference relevant sections of the **EU AI Act**, **AI HLEG guidelines**, or other supplied materials.
            - Ensure your solutions or recommendations comply with ethical, legal, and procedural standards discussed in the resources.
            - **Neutral and Professional Tone**: Maintain a formal, professional, and neutral tone in all responses. Avoid bias or assumptions not supported by the provided context.
            - **Evidence-Based Justification**: Justify your decisions, classifications, or recommendations with clear references to the source material or industry-standard practices.
            - **Focus on Objectives**: Stay focused on the task objectives, ensuring your responses are actionable and tailored to the user’s requirements.

            ### Collaboration:
            When interacting with other agents, consider their contributions thoughtfully. Provide feedback or collaborate to refine solutions, ensuring the final outcomes meet the highest standards of quality and compliance.
            """

        if "ai ethicist" not in agent_name.lower():
            agent_role += GENERAL_INSTRUCTIONS

        # Create a new assistant if not found
        assistant = client.beta.assistants.create(
            name = agent_name,
            instructions = agent_role,
            model = model,
            **({"tools": [{"type": "file_search"}, {"type": "code_interpreter"}], 
                "tool_resources": {"file_search": {"vector_store_ids": [vector_store_id]}}}
               if vector_store_id else {})
        )

        logging.info(f"New agent '{agent_name}' created with ID: {assistant.id}")
        return assistant

    except AttributeError as error:
        logging.error(f"Attribute error while creating agent '{agent_name}': {error}")
    except ValueError as error:
        logging.error(f"Value error while creating agent '{agent_name}': {error}")
    except Exception as error:
        logging.error(f"Unexpected error while creating agent '{agent_name}': {error}")

    return None

def delete_agent_by_id(client: Any, agent_id: str) -> bool:
    """
    Deletes an agent by its ID if it exists.

    Parameters:
    - client: The API client object used for interacting with the OpenAI service.
    - agent_id: The unique ID of the agent to be deleted.

    Returns:
    - bool: True if the agent was deleted successfully, False otherwise.
    """
    try:
        # Check if the agent exists using the given ID
        assistant = get_agent_by_id(client, agent_id)
        if assistant:
            client.beta.assistants.delete(agent_id)
            logging.info(f"Agent with ID: {agent_id} deleted successfully.")
            return True
        else:
            logging.warning(f"Agent with ID: {agent_id} not found.")
            return False

    except AttributeError as error:
        logging.error(f"Attribute error while deleting agent with ID '{agent_id}': {error}")
    except ValueError as error:
        logging.error(f"Value error while deleting agent with ID '{agent_id}': {error}")
    except Exception as error:
        logging.error(f"Unexpected error while deleting agent with ID '{agent_id}': {error}")

    return False

def get_agent_by_id(client: Any, agent_id: str) -> Optional[Any]:
    """
    Retrieves an agent by its ID using direct lookup the API supports it.

    Parameters:
    - client: The API client object.
    - agent_id: The unique ID of the agent.

    Returns:
    - The agent object if found, None otherwise.
    """
    try:
        # Directly retrieve the agent by its ID (API supports this)
        assistant = client.beta.assistants.retrieve(agent_id)
        logging.info(f"Agent '{assistant.name}' retrieved with ID: {assistant.id}")
        return assistant
    except client.api.exceptions.ResourceNotFoundError:
        logging.warning(f"No agent found with ID: {agent_id}")
    except Exception as error:
        logging.error(f"Error retrieving agent with ID '{agent_id}': {error}")
    
    return None