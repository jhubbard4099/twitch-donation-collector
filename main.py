
import threading

import twitchio_bot
import streamlabs_bot
import gspread_functions


def main() -> None:
    thread1 = threading.Thread(target=twitchio_bot.main)
    thread2 = threading.Thread(target=streamlabs_bot.main)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

if __name__ == "__main__":
    main()
