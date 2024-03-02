import pandas as pd
import yaml
import streamlit_authenticator as stauth

excel_file_path = "credentials.xlsx" 
df = pd.read_excel(excel_file_path)

names = df["user_name"].tolist()
ids = df["user_id"].tolist()
emails = df["email"].tolist()
passwords = df["password"].tolist()

hashed_passwords = stauth.Hasher(passwords).generate() # 비밀번호 해싱

# YAML 형식으로 변환
credentials_dict = {'credentials': {'usernames': {}}}
for user_id, name, email, hashed_password in zip(ids, names, emails, hashed_passwords):
    credentials_dict['credentials']['usernames'][user_id] = {
        'email': email,
        'name': name,
        'password': hashed_password
    }

additional_config = {
    'cookie': {
        'expiry_days': 0,
        'key': 'cookie_key_test',
        'name': 'cookie_name_test'
    },
    'preauthorized': {
        'emails': ['admin@gmail.com']
    }
}

config_dict = {**credentials_dict, **additional_config}

with open('config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config_dict, file, allow_unicode=True, sort_keys=False)


