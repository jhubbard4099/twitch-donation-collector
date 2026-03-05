import gspread

from os import getenv
from dotenv import load_dotenv


# Google Sheet equation constants
INSERTION_INDEX = 3
REGEX_STRING = "{([^}]+)}"
COL_E = f'=IFS(AND(ISNUMBER(SEARCH("hair", D{INSERTION_INDEX})), ISNUMBER(SEARCH("beard", D{INSERTION_INDEX}))), "either", ISNUMBER(SEARCH("hair", D{INSERTION_INDEX})), "hair", ISNUMBER(SEARCH("beard", D{INSERTION_INDEX})), "beard", true, "")'
COL_F = f'=IFS(AND(ISNUMBER(SEARCH("longer", D{INSERTION_INDEX})), ISNUMBER(SEARCH("shorter", D{INSERTION_INDEX}))), "either", ISNUMBER(SEARCH("longer", D{INSERTION_INDEX})), "longer", ISNUMBER(SEARCH("shorter", D{INSERTION_INDEX})), "shorter", true, "")'
COL_G = f'=IF(REGEXMATCH(D{INSERTION_INDEX}, "{REGEX_STRING}"), REGEXEXTRACT(D{INSERTION_INDEX}, "{REGEX_STRING}"), "")'
COL_H = f'=E{INSERTION_INDEX}'
COL_I = f'=F{INSERTION_INDEX}'
COL_J = f'=G{INSERTION_INDEX}'


# Load in private variables from environment
load_dotenv()
API_KEY: str = getenv("GSPREAD_API_KEY")
SH_URL: str = getenv("GSPREAD_SH_URL")

# Build worksheet access for service account
gc = gspread.service_account()
sh = gc.open_by_url(SH_URL)
worksheet = sh.get_worksheet(0)


def donationToRow(donator, amount, type, message):
    # Parameters:   values - Donator, Amount, Type, Message
    #               index - 3, to put them below header rows
    #               value_input_option - USER_ENTERED, so equations work properly
    worksheet.insert_row([donator, amount, type, message, COL_E, COL_F, COL_G, COL_H, COL_I, COL_J], 3, "USER_ENTERED")

def main() -> None:
    print(worksheet.acell("A1").value)
    print(worksheet.acell("A3").value)
    # worksheet.update_acell("A10", "TEST2")

    donationToRow("donator", 5.99, "type", "message beard shorter {red}")

if __name__ == "__main__":
    main()
