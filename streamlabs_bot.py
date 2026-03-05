from os import getenv
from dotenv import load_dotenv


# Load in private variables from environment
load_dotenv()
CLIENT_ID: str = getenv("STREAMLABS_CLIENT_ID")
CLIENT_SECRET: str = getenv("STREAMLABS_CLIENT_SECRET")
API_ACCESS_TOKEN: str = getenv("STREAMLABS_API_ACCESS_TOKEN")
SOCKET_API_TOKEN: str = getenv("STREAMLABS_SOCKET_API_TOKEN")


def main() -> None:
    print("test")

if __name__ == "__main__":
    main()
