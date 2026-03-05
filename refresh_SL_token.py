from os import getenv
from dotenv import load_dotenv
from subprocess import call


# Load in private variables from environment
load_dotenv()
CLIENT_ID: str = getenv("STREAMLABS_CLIENT_ID")
CLIENT_SECRET: str = getenv("STREAMLABS_CLIENT_SECRET")
REDIRECT_URL = "http://localhost:8080/auth"


"""
Command to run:
    curl --location 'https://streamlabs.com/api/v2.0/token' \
    --header 'Content-Type: application/json' \
    --header 'X-Requested-With: XMLHttpRequest' \
    --data '{
        "grant_type": "authorization_code",
        "client_id": "<client_id>",
        "client_secret": "<client_secret>",
        "redirect_uri": "https://test.streamlabs.com/auth",
        "code": "<code_from_authorization>"
    }'
"""
def main() -> None:
    authenticationCode = input("Enter authentication code: ")
    
    call([
        "curl", 
            "--location", "'https://streamlabs.com/api/v2.0/token'",
            "--header", "'Content-Type: application/json'",
            "--header", "'X-Requested-With: XMLHttpRequest'",
            "--data", "'{ \
                'grant_type': 'authorization_code', \
                'client_id': '{CLIENT_ID}', \
                'client_secret': '{CLIENT_SECRET}', \
                'redirect_uri': '{REDIRECT_URL}', \
                'code': '{authenticationCode}' \
                }'"
        ])

if __name__ == "__main__":
    main()
