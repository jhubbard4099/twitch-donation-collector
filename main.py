
import gspread
import twitchio_bot

from os import getenv
from dotenv import load_dotenv

# Load in private variables from environment
load_dotenv()
API_KEY: str = getenv("GSPREAD_API_KEY")
SH_URL: str = getenv("GSPREAD_SH_URL")

gc = gspread.api_key(API_KEY)
sh = gc.open_by_url(SH_URL)

def main() -> None:
    print(sh.sheet1.get('A1'))
    twitchio_bot.main()

if __name__ == "__main__":
    main()
