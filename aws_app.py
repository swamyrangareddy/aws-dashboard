import streamlit as st
import pandas as pd
from aws_braintap import BraninTapApp
from aws_braintap import Dashboard

# Configure the Streamlit page layout and settings
st.set_page_config(
    page_title="Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

# Authentication logic
def authenticate_user():
    """
    Authenticates the user using a JWT token entered in a password field.
    Sets session state based on the validity of the entered credentials.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False  # Initialize authentication status

    if st.session_state["authenticated"]:
        return True
    else:
        st.header("Dashboard App with JWT Authentication")
        st.text_input(
            label="Enter your JWT token:",
            value="",
            key="passwd",
            type="password"
        )
        st.button("Authenticate", on_click=validate_credentials)
        return False

def validate_credentials():
    """
    Validates the JWT token entered by the user. Sets the authenticated status
    in the session state based on the token validity.
    """
    token = st.session_state["passwd"].strip()
    if token == "stripe":
        st.session_state["authenticated"] = True
    else:
        st.session_state["authenticated"] = False
        if not token:
            st.warning("Please enter Password")
        else:
            st.error("Invalid JWT Token")

# Main application logic
def main():
    """
    Main function to run the dashboard application.
    Displays either the 'Braintap' or 'Stripe' dashboard based on user selection,
    accessible after successful authentication.
    """
    if authenticate_user():
        st.sidebar.title("Navigation")
        selected_page = st.sidebar.radio("Select a page", ( "Stripe","Braintap"))

        # Initialize and run the selected page's main application
        if selected_page == "Braintap":
            app = BraninTapApp()
            app.main()
        elif selected_page == "Stripe":
            dashboard = Dashboard()
            dashboard.main()

if __name__ == "__main__":
    main()
