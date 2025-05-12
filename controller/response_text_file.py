from io import StringIO

def generate_conversation_text(conversation_history, agents, project_description):
    """
    Generate a text version of the conversation with agent names, instructions, and project description.

    Parameters:
    - conversation_history: List of conversation responses.
    - agents: List of agent details (name and role).
    - project_description: Description of the project.

    Returns:
    - Text content to be saved in a file.
    """
    text_content = StringIO()
    
    text_content.write("Project Description:\n")
    text_content.write(f"{project_description}\n\n")
    
    text_content.write("Agents:\n")
    for agent in agents:
        if agent['name'] != "AI Ethicist":
            text_content.write(f"Name: {agent['name']}\n")
            text_content.write(f"Instructions: {agent['role']}\n\n")
    
    text_content.write("Conversation History:\n")
    for entry in conversation_history:
        # Convert entry to a string if it's not already a string
        text_content.write(str(entry) + "\n")
    
    return text_content.getvalue()
