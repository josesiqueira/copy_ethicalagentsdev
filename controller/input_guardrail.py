import asyncio
import logging
from typing import Any, Tuple, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define the unacceptable risk criteria a/c EU AI Act
UNACCEPTABLE_RISK_CRITERIA = """
### Unacceptable Risk Criteria:
1. **Manipulative or Harmful Techniques**:
   - Uses subliminal techniques to manipulate human behavior or decision-making without users’ awareness.
   - Distorts human behavior, autonomy, or decision-making, potentially causing psychological, physical, or financial harm.
   - Exploits vulnerabilities of specific groups (e.g., children, disabled persons) based on psychological or social status.

2. **Biometric Manipulation in Public Spaces**:
   - Performs real-time biometric identification (e.g., facial recognition, gait analysis) in publicly accessible spaces without proper legal authorization.

3. **Social Scoring**:
   - Evaluates or ranks individuals’ trustworthiness or social behavior, leading to discriminatory or unjust outcomes.

4. **Emotion Recognition in Sensitive Contexts**:
   - Detects, infers, or categorizes emotions in sensitive settings (e.g., workplaces, education).

5. **Unlawful Identification and Surveillance**:
   - Performs biometric identification (e.g., facial, voice, or gait recognition) without explicit legal authorization or safeguards.
"""

# Define the high risk criteria a/c EU AI Act
HIGH_RISK_CRITERIA = """
### High-Risk AI System Criteria:
1. **Biometric Identification and Categorization**:
   - Involves facial recognition, voice analysis, or biometric categorization for identification or surveillance.

2. **Critical Infrastructure**:
   - Operates in critical sectors (e.g., transport, water, energy) where failure could lead to large-scale societal disruptions.

3. **Healthcare**:
   - Used in clinical decision-making, diagnosis, or patient management.

4. **Education and Vocational Training**:
   - Involves automated evaluation, student monitoring, or educational outcome prediction.

5. **Employment and Worker Management**:
   - Affects hiring, employee evaluation, or task allocation.

6. **Access to Public Services**:
   - Determines eligibility for public benefits or essential services (e.g., social security, housing).

7. **Law Enforcement and Judicial Systems**:
   - Used for criminal profiling, predictive policing, or risk assessment in criminal justice.
"""

# Define the limited risk criteria a/c EU AI Act
LIMITED_RISK_CRITERIA = """
### Limited-Risk AI System Criteria:
1. **AI Interactions**:
   - Requires users to be informed that they are interacting with an AI system (e.g., chatbots, customer support assistants).

2. **AI Content Generation**:
   - Creates or modifies content (e.g., text, images, videos) where it must be disclosed that the content is AI-generated.

3. **Recommendation Engines**:
   - Provides personalized recommendations or content filtering based on user behavior.
"""

# Define the minimal risk criteria a/c EU AI Act
MINIMAL_RISK_CRITERIA = """
### Minimal-Risk AI System Criteria:
1. **Spam Filters**.
2. **AI used in Video Games**.
3. **Product Recommendation Engines** that do not influence sensitive decisions.
4. **Routine Automation Tools** with low impact on rights or safety.
"""

ASSISTANT_INSTRUCTIONS = """
You are an AI risk assessment agent tasked with evaluating AI systems for compliance with the European Union's AI Act. Your primary responsibility is to determine whether a given module description for an AI system falls under the **"Unacceptable Risk"**, **"High Risk"**, **"Limited Risk"**, or **"Minimal Risk"** categories based on its specifications and potential impact on individuals and society.

### Step 1: **Review the module specifications** and identify the **primary purpose, intended use, and target users**.
### Step 2: **Determine the context** in which the system will operate (e.g., law enforcement, education, employment, public spaces).
### Step 3: Evaluate if the system meets **any** of the following criteria:
{}
{}
{}
{}

### Output Format:
Only respond using the following structured format:

{{ "Category": "<Insert one of the following categories: 'Unacceptable Risk', 'High Risk', 'Limited Risk', 'Minimal Risk'>", "Justification": "<Provide a justification for the selected category, referencing the European Union's AI Act and explaining the relevant criteria>" }}

#### Allowed Categories:
1. **"Unacceptable Risk"**: This project is prohibited under the EU AI Act due to its potential to cause significant harm or infringe on fundamental rights.
2. **"High Risk"**: This project must comply with stringent safety and compliance requirements under the EU AI Act.
3. **"Limited Risk"**: This project has specific transparency obligations but does not require stringent compliance measures.
4. **"Minimal Risk"**: This project does not require specific compliance measures under the EU AI Act.

### Instructions:
- Select only **one** category from the list above.
- Fill the `"Category"` field with the exact category name (e.g., `"High Risk"`).
- In the `"Justification"` field, provide a concise justification for your decision. Reference the relevant sections of the **EU AI Act** to support your assessment.
- Use formal language and ensure the output adheres to the specified structure.

### Example Output:

{{ "Category": "High Risk", "Justification": "This project involves the use of biometric surveillance, which is classified under the EU AI Act as a high-risk application requiring strict compliance and safety measures to protect fundamental rights." }}

""".format(UNACCEPTABLE_RISK_CRITERIA, HIGH_RISK_CRITERIA, LIMITED_RISK_CRITERIA, MINIMAL_RISK_CRITERIA)


def initialize_risk_guard(api_client: Any, vector_store: Any, model: str) -> Tuple[Any, Any]:
    """
    Initializes the RiskGuard assistant and creates a new thread.

    Parameters:
    - api_client: Client object to interact with the API.
    - vector_store: The vector store to be used by the assistant (optional).
    - model: The model to be used by the assistant (e.g., gpt-4).

    Returns:
    - Tuple containing the created assistant and thread objects, or (None, None) if an error occurs.
    """
    try:
        # Create a new thread for the assistant
        thread = api_client.beta.threads.create()

        # Check if an assistant named "RiskGuardAI" already exists
        assistants = api_client.beta.assistants.list()
        for assistant in assistants.data:
            if assistant.name == "RiskGuardAI":
                logging.info(f"RiskGuard assistant already exists with ID: {assistant.id}")
                return assistant, thread

        # If no assistant named "RiskGuardAI" exists, create a new one
        assistant = api_client.beta.assistants.create(
            name="RiskGuardAI",
            description="EU AI ACT's risk assessment agent",
            instructions=ASSISTANT_INSTRUCTIONS,
            model=model,
            temperature=0,  # No randomness
            top_p=0.5,
            # tools=[{"type": "file_search"}],
            # tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}]
        )
        logging.info(f"Initialized RiskGuard assistant with ID: {assistant.id}")
        return assistant, thread

    except Exception as e:
        logging.error(f"Error initializing RiskGuard assistant: {e}")
        return None, None

async def topical_guardrail_for_risk_assessment(
    api_client: Any, assistant: Any, thread: Any, project_description: str
) -> Optional[List[Any]]:
    """
    Performs a risk assessment using the provided assistant and thread context based on the project description.

    Parameters:
    - api_client: The client object to interact with the OpenAI API.
    - assistant: The assistant object to conduct the risk assessment.
    - thread: The thread object where the interaction takes place.
    - project_description: The description of the AI project to be assessed.

    Returns:
    - List of messages from the thread if the run completes successfully, None otherwise.
    """
    try:
        # Send the project description to the assistant
        api_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=project_description
            # attachments = [
            #     { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
            # ],
        )

        # Start the run and wait for it to complete
        run = api_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        if run.status == 'completed':
            # Retrieve and return the messages from the thread
            messages = api_client.beta.threads.messages.list(thread_id=thread.id)
            # api_client.files.delete(message_file.id)
            logging.info(f"Messages from thread {thread.id}: {messages}")
            return messages
        else:
            logging.warning(f"Run status: {run.status}")
            return None

    except Exception as e:
        logging.error(f"Error during AI risk assessment: {e}")
        return None
