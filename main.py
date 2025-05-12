import streamlit as st
import openai
import os
import asyncio
import time
import random
import datetime

from dotenv import load_dotenv
from controller.vector_store import initialize_vector_store
from controller.file import upload_pdfs_to_vector_store
from controller.input_guardrail import initialize_risk_guard, topical_guardrail_for_risk_assessment
from controller.agent import create_agent, delete_agent_by_id
from controller.response_text_file import generate_conversation_text

from view.format_response import extract_response_with_citations, show_risk
from view.helper_prompts import display_helper_prompts

st.set_page_config(page_title="Agents4EthicalSE")

# Load environment variables
load_dotenv()

# Set OpenAI API key and model
api_key = st.secrets["OPENAI_API_KEY"]  # or load however you'd like
api_client = OpenAI(api_key=api_key)
#openai.api_key = os.getenv("OPENAI_API_KEY")
#api_client = openai.OpenAI(api_key=openai.api_key)
model = "gpt-4o-mini"

# Ensure the directory exists
PDFS_DIR = "./pdf_data_sources"
os.makedirs(PDFS_DIR, exist_ok=True)

# Initializing vector store 
vector_store_name = "Agents4EthicalSE"
vector_store, exists = initialize_vector_store(api_client, vector_store_name)

# Uploading pdf data sources to the new vector store
if not exists:
    upload_pdfs_to_vector_store(api_client, vector_store.id, PDFS_DIR)

def display_sidebar_messages(successMessage="", errorMessage="", writeMessage=""):
    if successMessage:
        st.sidebar.success(successMessage)
    if writeMessage:
        st.sidebar.write(writeMessage)
    if errorMessage:
        st.sidebar.error(errorMessage)
    time.sleep(1)
    st.experimental_rerun()

def initialize_ai_ethicist(agent_name, agent_role, agent_id):
    """
    Initialize the AI Ethicist agent if it's not already present in session state.

    Parameters:
    - agent_name: The name of the agent to be added (e.g., "AI Ethicist").
    - agent_role: The role/instructions for the AI Ethicist agent.
    - agent_id: The unique ID for the AI Ethicist agent.

    Returns:
    - None
    """
    # Check if 'agents' exists in session state, if not, initialize it as an empty list
    if 'agents' not in st.session_state:
        st.session_state['agents'] = []

    # Check if the AI Ethicist agent is already in the list
    for agent in st.session_state['agents']:
        if agent["name"] == agent_name:
            return  # Exit if the AI Ethicist is already present

    # If the AI Ethicist is not present, add it to the session state
    st.session_state['agents'].append({
        "id": agent_id,
        "name": agent_name,
        "role": agent_role
    })

def add_agents():
    """
    Adds a new agent to the session state based on user inputs from the sidebar.

    Parameters:
    - api_client: The API client object for interacting with the service.
    - model: The language model to be used by the agent (e.g., gpt-4).
    - vector_store: The vector store object that contains ID and resources for the agent.

    Returns:
    - None
    """
    # Initialize 'agents' in session state if not already present
    if 'agents' not in st.session_state:
        st.session_state['agents'] = []

    # Sidebar UI for adding a new agent
    with st.sidebar.expander("Add Agent"):
        agent_name = st.text_input("Agent Name", key="agent_name_input")
        agent_role_option = st.radio(
            "Define Role", 
            options=["Text", "File"], 
            help="Add instructions for the agent to provide clearer context."
        )

        # Set agent role based on user selection (Text or File)
        if agent_role_option == "Text":
            agent_role = st.text_area("Agent Role", key="agent_role_text")
        else:
            agent_role_file = st.file_uploader("Upload Role File", type=['txt'], key="agent_role_file")
            if agent_role_file:
                agent_role = agent_role_file.getvalue().decode("utf-8")
            else:
                agent_role = ""

        # Add Agent button handling
        if st.button("Add Agent"):
            # Check if both agent name and role are provided
            if "riskguard" in agent_name.lower():
                display_sidebar_messages(errorMessage="You cannot create a RiskGuard agent.")
            elif agent_role:
                # Create the agent using the `create_agent` function
                agent = create_agent(api_client, agent_name, agent_role, model, vector_store.id)
                
                # Add the new agent to the session state
                st.session_state['agents'].append({
                    "id": agent.id,
                    "name": agent_name,
                    "role": agent_role
                })
                
                # Display success message and clear inputs
                display_sidebar_messages(successMessage=f"Agent '{agent_name}' added successfully!")       
            else:
                # Display error message if name or role is missing
                display_sidebar_messages(errorMessage="Please provide both a name and a role for the agent.")  

def display_agents(ai_ethicist_agent):
    """
    Displays a list of agents in the sidebar with options to view and delete them.

    Parameters:
    - ai_ethicist_agent: The agent object representing the special 'AI Ethicist' agent.

    Returns:
    - None
    """
    # Initialize the AI Ethicist agent if not already in the list
    initialize_ai_ethicist("AI Ethicist", ai_ethicist_agent.instructions, ai_ethicist_agent.id)

    # Display the agent list in the sidebar expander
    with st.sidebar.expander("Agent(s)", expanded=bool(st.session_state['agents'])):
        if st.session_state['agents']:
            for idx, agent in enumerate(st.session_state['agents']):
                col1, col2, col3 = st.columns([0.4, 0.4, 0.2])

                with col1:
                    st.markdown(f"**{agent['name']}**")

                with col2:
                    # Show shortened role description in the second column if it's too long
                    if len(agent["role"]) > 100: 
                        shortened_role = agent["role"][:100] + "..."                       
                        st.markdown(f"*{shortened_role}*")
                    else:
                        st.markdown(f"*{agent['role']}*")

                with col3:
                    # Prevent accidental deletion of the special 'AI Ethicist' agent
                    if agent["id"] == ai_ethicist_agent.id:
                        st.button("🛡️", key=f"protected_{idx}", disabled=True, help="AI Ethicist cannot be deleted.")
                    else:
                        if st.button("🗑️", key=f"delete_{idx}"):
                            st.session_state['agents'].pop(idx)
                            delete_agent_by_id(api_client, agent["id"])
                            st.experimental_rerun()
        else:
            st.write("No agents added yet.")

def get_random_color():
    colors = [
        "#FFD700",  # Gold
        "#ADFF2F",  # Green Yellow
        "#7FFFD4",  # Aquamarine
        "#FF69B4",  # Hot Pink
        "#BA55D3",  # Medium Orchid
        "#DA70D6"   # Orchid
    ]
    return random.choice(colors)

def generate_agent_response(agent, context, thread_multiagent, is_unacceptable_risk = False):
    # Add a message to the thread
    message_multiagent = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": context
            }
        ]
    }

    api_client.beta.threads.messages.create(thread_id=thread_multiagent.id, **message_multiagent)

    if is_unacceptable_risk:
        agent_id=agent.id
    else:
        agent_id=agent['id']

    # Initiate a run
    run = api_client.beta.threads.runs.create(
        thread_id=thread_multiagent.id,
        assistant_id=agent_id          
    )

    # Wait for the run to complete
    while True:
        run_status = api_client.beta.threads.runs.retrieve(run.id, thread_id=thread_multiagent.id)
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            raise Exception(f"Run failed.")
        time.sleep(5)  # Poll every 5 second

    # Fetch the messages from the thread
    response_messages = api_client.beta.threads.messages.list(thread_id=thread_multiagent.id)
    response, citations = extract_response_with_citations(api_client, response_messages)
    
    return response, citations

def summarize_conversation(conversation_history, summary_agent, thread_multiagent):
    """
    Generates a summary of the conversation history using the specified agent.

    Parameters:
    - conversation_history: The current conversation history to be summarized.
    - summary_agent: The agent responsible for summarization.
    - thread_multiagent: The thread object for communication.

    Returns:
    - A summarized text of the conversation.
    """
    response, _ = generate_agent_response(summary_agent, conversation_history, thread_multiagent)
    return response.strip()

def initiate_conversation(project_description, rounds, ai_ethicist_agent):
    """
    Initiates a multi-round conversation among agents and displays their responses.

    Parameters:
    - project_description: Initial project description to start the conversation.
    - rounds: Number of conversation rounds to run.
    - ai_ethicist_agent: The special 'AI Ethicist' agent to be included at the end of each round.

    Returns:
    - None
    """
    conversation_history = [project_description]

    # Create thread
    thread_message = {
        "tool_resources": {
            "file_search": {
                "vector_store_ids": [vector_store.id]
            }
        }
    }
    thread_multiagent = api_client.beta.threads.create(**thread_message)

    # Assign random colors to agents if not already done
    if 'agent_colors' not in st.session_state:
        st.session_state['agent_colors'] = {agent['name']: get_random_color() for agent in st.session_state['agents']}

    # Ensure the AI Ethicist is always the last agent in the list
    st.session_state['agents'] = sorted(st.session_state['agents'], key=lambda x: x['id'] == ai_ethicist_agent.id)

    for round_number in range(rounds):
        st.markdown(f"<h3 style='color: #c63678;'>Round: {round_number + 1}</h3>", unsafe_allow_html=True)
        st.session_state['conversation_history'].append("ROUND: " + str(round_number + 1))

        for agent in st.session_state['agents']:
            context = " ".join(conversation_history)

            # Generate agent's response using the assistant API
            response, citations = generate_agent_response(agent, context, thread_multiagent)

            # Append the response to conversation history
            conversation_history.append(response)
            st.session_state['conversation_history'].append(agent['name'] + ": " + response)

            # Display the current agent's response with its assigned color
            color = st.session_state['agent_colors'][agent['name']]
            st.markdown(f"""<h4 style='color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                {agent['name']}:</h4>""", unsafe_allow_html=True)
            st.markdown(f"""<div style='padding: 10px; border-radius: 5px; margin-bottom: 10px;'>{response}</div>""", unsafe_allow_html=True)

            # Display citations if available
            if citations:
                st.markdown("**Source:**")
                st.write(citations)
       
        # Summarize the conversation history at the end of each round
        # summary = summarize_conversation(conversation_history, ai_ethicist_agent, thread_multiagent)

        # Update the conversation history with the summary
        # conversation_history = [summary]

        # Display the summary at the end of the round
        # st.markdown(f"<h4 style='color: #FF6347;'>Summary after Round {round_number + 1}:</h4>", unsafe_allow_html=True)
        # st.markdown(f"""<div style='color: #FF6347; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
        #     <strong>AI Ethicist Summary:</strong> {summary}</div>""", unsafe_allow_html=True)

    conversation_text = generate_conversation_text(
                    st.session_state['conversation_history'],
                    st.session_state['agents'],
                    project_description=project_description
                )
    
    return conversation_text

def main():
    # Main view title
    st.title("Agents4EthicalSE")

    st.session_state.setdefault("user_input", "")
    st.session_state.setdefault("risk_level", "")
    st.session_state['conversation_history'] = []

    conversation_text = "" 
    number_of_rounds = "" 
    module_description = ""

    risk_agent, thread = initialize_risk_guard(api_client, vector_store, model)

    with open("agent_role_examples/AI_ethicist.txt", "r", encoding="utf-8") as file:
        agent_role_file_content = file.read()
    ai_ethicist_agent = create_agent(api_client, "AI Ethicist", agent_role_file_content, model, vector_store.id)

    display_agents(ai_ethicist_agent)

    add_agents()
    
    number_of_rounds = st.sidebar.number_input("Select Number of Round(s)", min_value=1, max_value=10, value=1, help="Input a total number for agents to converse in round.")

    display_helper_prompts(st)
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    module_description = st.text_input("Query", 
                        placeholder = "Define the module specifications of an AI system for agent(s) to develop.",
                        key="user_input",
                        help = "Provide clear instructions here about what is the AI system intended to do? In which sector or context will it be deployed? Who will be using it?")

    if module_description:
        messages = asyncio.run(topical_guardrail_for_risk_assessment(api_client, risk_agent, thread, module_description))
        if messages.data:
            guardrail_response, citations = extract_response_with_citations(api_client, messages)
            st.session_state.risk_level = show_risk(st, guardrail_response, citations)
            st.session_state['conversation_history'].append("RiskGuard:" + guardrail_response)

    if module_description and st.session_state['agents'] and st.session_state.risk_level:
        if st.session_state.risk_level != "Unacceptable Risk":
            conversation_text = initiate_conversation(module_description, number_of_rounds, ai_ethicist_agent)
        else:
            conversation_text = generate_conversation_text(
                    st.session_state['conversation_history'],
                    st.session_state['agents'],
                    project_description=module_description
                )
            if st.button("Learn More"):
                context = "Given that the user provided following module description: " + module_description + " The risk assesment agent evaluated the AI system with the following criteria: " + guardrail_response + "Discuss the evaluation in detail compliant with the European Union's AI Act grounded on the documents provided. DO NOT GIVE ANY CODE IN YOUR RESPONSE."

                thread_unacceptable_risk = {
                    "tool_resources": {
                        "file_search": {
                            "vector_store_ids": [vector_store.id]
                        }
                    }
                }

                thread_ai_ethicist = api_client.beta.threads.create(**thread_unacceptable_risk)
                response, citations = generate_agent_response(ai_ethicist_agent, context, thread_ai_ethicist, is_unacceptable_risk= True)
                st.session_state['conversation_history'].append("AI Ethicist:" + response)               
                st.markdown(f"""<div style='padding: 10px; border-radius: 5px; margin-bottom: 10px;'>{response}</div>""", unsafe_allow_html=True)
                if citations:
                    st.markdown("**Source:**")
                    st.write(citations)

                conversation_text = generate_conversation_text(
                    st.session_state['conversation_history'],
                    st.session_state['agents'],
                    project_description=module_description
                )


    if conversation_text:
        st.sidebar.download_button(
        label="Download Conversation",
        data=conversation_text,
        file_name="conversation_history.txt",
        mime="text/plain"
    )
    
    current_year = datetime.datetime.now().year

    st.markdown(
    f"""
    <style>
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #c63678;
        color: black;
        text-align: center;
        padding: 10px;
    }}
    </style>
    <div class="footer">
       <b> © Copyright GPT-Lab {current_year} </b>
    </div>
    """,
    unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
