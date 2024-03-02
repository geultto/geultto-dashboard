import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dashboard import display_dashboard

st.set_page_config(page_title="글또 운영대시보드",
                layout="wide",
                initial_sidebar_state="expanded"
                )

def main():

    # config 로드
    with open('account/config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login()

    if authentication_status:
        authenticator.logout(location='sidebar')
        display_dashboard(name)
    else:
        if st.session_state.get("authentication_status") is False:
            st.error('Username/password is incorrect')

if __name__ == '__main__':
    main()
