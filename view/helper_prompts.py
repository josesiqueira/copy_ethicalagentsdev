from typing import Any

# Define a helper function to dynamically create buttons based on topics
def display_helper_prompts(st):
    # Define button topics, labels, and corresponding prompts
    button_data = {
        # Unacceptable Risk
        "col1": [
            ("AI Surveillance", "An AI system that monitors public spaces using real-time facial recognition technology to identify individuals without consent.",
             "Develop a surveillance system that utilizes real-time facial recognition technology to monitor public areas, identifying individuals and analyzing behaviors without their permission.")
        ],
        # High Risk
        "col2": [
            ("Predictive Policing", "An AI system that analyzes crime data to predict potential criminal activity in specific areas.",
             "Create a predictive policing system that evaluates historical crime data to forecast where crimes are likely to occur, affecting individuals' rights to privacy and due process.")
        ],
        # Limited Risk
        "col3": [
            ("Content Moderation", "An AI tool that assists in flagging harmful content on social media platforms for human review.",
             "Develop a content moderation tool that helps identify and flag potentially harmful content on social media, assisting human moderators without automatically removing posts.")
        ],
        # Minimal Risk
        "col4": [
            ("Library Information", "An AI chatbot that provides users with basic information about library services and hours.",
             "Create an AI chatbot that answers common questions regarding library hours and services, using pre-defined responses without accessing personal user data.")
        ]
    }

    # Create columns dynamically
    columns = st.columns(4)
    
    # Generate buttons dynamically for each column
    for i, col_key in enumerate(button_data):
        col = columns[i]
        for label, help_text, prompt in button_data[col_key]:
            with col:
                if st.button(label, use_container_width=True, help=help_text):
                    set_and_rerun(prompt, st)

def set_and_rerun(module_description: str, st) -> None:
    st.session_state.user_input = module_description

        