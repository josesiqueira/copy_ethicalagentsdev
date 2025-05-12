from typing import Tuple, List, Any
import json

def extract_response_with_citations(client: Any, response_messages: Any) -> Tuple[str, List[str]]:
    """
    Extracts the assistant's response and formats citations from the given response messages.

    Parameters:
    - client: The client object to interact with the file service.
    - response_messages: The response messages object containing the assistant's messages.

    Returns:
    - Tuple[str, List[str]]: A tuple containing the formatted response text and a list of citations.
    """
    response_text = ""
    citations = []

    # Iterate through response messages to find the assistant's response
    for message in response_messages.data:
        if message.role == "assistant" and message.content:
            message_content = message.content[0].text
            annotations = message_content.annotations

            # Replace annotated text with citation indices and generate citations list
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(
                    annotation.text, f"<span style='color: #B22222;'><b>[{index}]</b></span>"
                )
                # Retrieve the file citation if present and format it
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            # Set the response text to the formatted content
            response_text = message_content.value
            break  # Only process the first assistant response

    return response_text.strip(), citations

def show_risk(st, response: str, citations: list) -> str:
    """
    Displays the response text in a colored tile based on the detected risk category and returns the risk level.

    Parameters:
    - response: The response text from the AI assessment, expected to be a JSON string with "Category" and "Justification".
    - citations: A list of citations associated with the response.

    Returns:
    - str: The detected risk level/category.
    """
    # Determine the risk level from the response text
    if "Unacceptable Risk" in response:
        tile_color = "#B22222"  # Dark Red (Firebrick)
        risk_level = "Unacceptable Risk"
    elif "High Risk" in response:
        tile_color = "#FF8C00"  # Dark Orange
        risk_level = "High Risk"
    elif "Limited Risk" in response:
        tile_color = "#40E0D0"  # Dark Yellow (Gold)
        risk_level = "Limited Risk"
    elif "Minimal Risk" in response:
        tile_color = "#228B22"  # Dark Green (Forest Green)
        risk_level = "Minimal Risk"
    else:
        tile_color = "#A9A9A9"  # Dark Gray (Default)
        risk_level = "Unknown Risk"

    # Convert the response string to a dictionary
    try:
        data_dict = json.loads(response)
        category = data_dict.get("Category", "N/A")
        justification = data_dict.get("Justification", "N/A")
    except json.JSONDecodeError:
        category = "Risk associated to the system unidentified"
        justification = "Invalid response format."

    # Format the response text with citations if available
    formatted_response = justification
    if citations:
        formatted_response += "\n\n### Citations:\n" + "\n".join(citations)

    # Create a styled container using Markdown and HTML
    st.markdown(
        f"""
        <div style='background-color: {tile_color}; padding: 15px; border-radius: 10px; margin-bottom: 5px'>
            <h2>{category}</h2>
            <p>Justification:{formatted_response}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Return the detected risk level
    return risk_level