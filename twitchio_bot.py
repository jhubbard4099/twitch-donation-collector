"""
An example of connecting to a conduit and subscribing to EventSub when a User Authorizes the application.

This bot can be restarted as many times without needing to subscribe or worry about tokens:
- Tokens are stored in '.tio.tokens.json' by default
- Subscriptions last 72 hours after the bot is disconnected and refresh when the bot starts.

Consider reading through the documentation for AutoBot for more in depth explanations.
"""

import asyncio
import logging
import random
from typing import TYPE_CHECKING

import asqlite
from os import getenv
from dotenv import load_dotenv

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

import donation_helper as dono
import gspread_functions as sheet


if TYPE_CHECKING:
    import sqlite3

LOGGER: logging.Logger = logging.getLogger("Bot")


# Load in private variables from environment
load_dotenv()
CLIENT_ID: str = getenv("TWITCHIO_CLIENT_ID") # The CLIENT ID from the Twitch Dev Console
CLIENT_SECRET: str = getenv("TWITCHIO_CLIENT_SECRET")  # The CLIENT SECRET from the Twitch Dev Console
BOT_ID = getenv("BOT_ID")  # The Account ID of the bot user...
OWNER_ID = getenv("OWNER_ID")  # Your personal User ID..


"""
Class representing an AutoBot, with all necessary initilization and functions
"""
class Bot(commands.AutoBot):

    # Init function
    def __init__(self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]) -> None:
        self.token_database = token_database

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
        )

    # Create hooks to the desired components
    async def setup_hook(self) -> None:
        # Add our components, which contain all commands and listeners
        await self.add_component(CommandTestComponent(self))
        await self.add_component(EventSubTestComponent(self))

    # Check tokens to perform OAuth authorization
    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel
            return

        # A list of subscriptions we would like to make to the newly authorized channel
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
            eventsub.ChannelPollBeginSubscription(broadcaster_user_id=payload.user_id),
            eventsub.ChannelBitsUseSubscription(broadcaster_user_id=payload.user_id),
            eventsub.ChannelSubscribeSubscription(broadcaster_user_id=payload.user_id),
            eventsub.ChannelSubscriptionGiftSubscription(broadcaster_user_id=payload.user_id),
            eventsub.ChannelSubscribeMessageSubscription(broadcaster_user_id=payload.user_id),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

    # Add user and bot tokens to database
    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    # Confirm bot is ready for use
    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)


"""
A test component with some EventSub listeners.
Made to test how to access subscription events.
"""
class EventSubTestComponent(commands.Component):

    # Example listener for an EventSub command
    @commands.Component.listener()
    async def event_poll_begin(self, payload: twitchio.ChannelPollBegin) -> None:
        print(f"----- POLL STARTED -----")

        # Send to spreadsheet (for testing)
        sheet.donationToRow("TwitchIO", 4.99, "Test Donation", "TwitchIO poll start test")

    # Event listener for bit donations
    @commands.Component.listener()
    async def event_bit_use(self, payload: twitchio.ChannelBitsUse) -> None:
        # Debug prints
        print(f"----- BIT DONATION -----")
        msg = f"thank you {payload.user.name} for the {payload.bits} bits, used for {payload.type}!! (timestamp: {payload.timestamp}, fragments: {payload.fragments}, power-up: {payload.power_up}, text: '{payload.text}',)"
        print(msg)
        print(f"----- BIT DONATION -----")

        # Build spreadsheet row info
        donator = payload.user.name
        amount = dono.findBitAmount(payload.bits)
        type = "Bits"
        message = payload.text

        # Send to spreadsheet, only if total amount is $1.00 or more
        if amount >= 1.00:
            sheet.donationToRow(donator, amount, type, message)

    # Event listener for standard channel subscriptions
    @commands.Component.listener()
    async def event_subscription(self, payload: twitchio.ChannelSubscribe) -> None:
        # Debug prints
        print(f"----- STANDARD SUBSCRIPTION -----")
        msg = f"thank you {payload.user.name} for the tier {payload.tier} sub!! (timestamp: {payload.timestamp}, gift: {payload.gift})"
        print(msg)
        print(f"----- STANDARD SUBSCRIPTION -----")

        # Build spreadsheet row info
        donator = payload.user.name
        amount = dono.findSubAmount(payload.tier)
        type = f"Tier {dono.findSubType(payload.tier)} Sub"
        message = ""

        # Send to spreadsheet, only if not given from a gift sub
        if not payload.gift:
            sheet.donationToRow(donator, amount, type, message)

    # Event listener for gifted channel subscriptions
    @commands.Component.listener()
    async def event_subscription_gift(self, payload: twitchio.ChannelSubscriptionGift) -> None:
        # Debug prints
        print(f"----- GIFT SUBSCRIPTION -----")
        msg = f"thank you {payload.user.name} for the {payload.total} tier {payload.tier} sub(s)!! (timestamp: {payload.timestamp}, anonymous: {payload.anonymous}, total: {payload.cumulative_total})"
        print(msg)
        print(f"----- GIFT SUBSCRIPTION -----")

        # Build spreadsheet row info
        donator = payload.user.name
        amount = dono.findSubAmount(payload.tier) * payload.total
        type = f"{payload.total} Tier {dono.findSubType(payload.tier)} Gift Sub(s)"
        message = ""

        # Send to spreadsheet
        sheet.donationToRow(donator, amount, type, message)


    # Event listener for renewed channel subscriptions
    @commands.Component.listener()
    async def event_subscription_message(self, payload: twitchio.ChannelSubscriptionMessage) -> None:
        # Debug prints
        print(f"----- RENEW SUBSCRIPTION -----")
        msg = f"thank you {payload.user.name} for the {payload.months} month tier {payload.tier} sub!! (timestamp: {payload.timestamp}, cumulative months: {payload.cumulative_months}, streak: {payload.streak_months}, text: '{payload.text}', emotes: {payload.emotes})"
        print(msg)
        print(f"----- RENEW SUBSCRIPTION -----")

        # Build spreadsheet row info
        donator = payload.user.name
        amount = dono.findSubAmount(payload.tier)
        type = f"Tier {dono.findSubType(payload.tier)} Renew Sub"
        message = payload.text

        # Send to spreadsheet
        sheet.donationToRow(donator, amount, type, message)


"""
A test component with some simple commands and listeners.
Made to test some basic chat command functionality.
"""
class CommandTestComponent(commands.Component):

    # Example listener for reading in chat messages
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        print(f"[{payload.broadcaster.name}] - ({payload.timestamp}) {payload.chatter.name}: {payload.text}")

        # Check for donation command sent by me or the bot through Streamlabs Chatbot program
        # Nest if checks to avoid doing the message splitting unless it could be sent from me or the bot
        if (payload.chatter.name == "jbot37x" or payload.chatter.name == "jman37x"):

            # Split message on spaces
            messageContents = payload.text.split()

            if messageContents[0] == "!donation":
                print(f"----- TIP DONATION -----")

                # Build spreadsheet row info
                donator = messageContents[1]
                amount = messageContents[2]
                donationMsg = " ".join(messageContents[3:])

                # Send to spreadsheet
                sheet.donationToRow(donator, amount, "Donation", donationMsg)

                print(f"----- TIP DONATION -----")

    @commands.command()
    async def hi(self, ctx: commands.Context) -> None:
        """
        Command that replies to the invoker with Hi <name>!

        !hi
        """
        await ctx.reply(f"Hi {ctx.chatter}!")

    @commands.command()
    async def say(self, ctx: commands.Context, *, message: str) -> None:
        """
        Command which repeats what the invoker sends.

        !say <message>
        """
        await ctx.send(message)

    @commands.command()
    async def add(self, ctx: commands.Context, left: int, right: int) -> None:
        """
        Command which adds to integers together.

        !add <number> <number>
        """
        await ctx.reply(f"{left} + {right} = {left + right}")

    @commands.command()
    async def choice(self, ctx: commands.Context, *choices: str) -> None:
        """
        Command which takes in an arbitrary amount of choices and randomly chooses one.

        !choice <choice_1> <choice_2> <choice_3> ...
        """
        await ctx.reply(f"You provided {len(choices)} choices, I choose: {random.choice(choices)}")

    @commands.command(aliases=["thanks", "thank"])
    async def give(self, ctx: commands.Context, user: twitchio.User, amount: int, *, message: str | None = None) -> None:
        """
        A more advanced example of a command which has makes use of the powerful argument parsing, 
        argument converters and aliases.

        The first argument will be attempted to be converted to a User.
        The second argument will be converted to an integer if possible.
        The third argument is optional and will consume the reast of the message.

        !give <@user|user_name> <number> [message]
        !thank <@user|user_name> <number> [message]
        !thanks <@user|user_name> <number> [message]
        """
        msg = f"with message: {message}" if message else ""
        await ctx.send(f"{ctx.chatter.mention} gave {amount} thanks to {user.mention} {msg}")

    @commands.group(invoke_fallback=True)
    async def socials(self, ctx: commands.Context) -> None:
        """
        Group command for our social links.

        !socials
        """
        await ctx.send("discord.gg/..., youtube.com/..., twitch.tv/...")

    @socials.command(name="discord")
    async def socials_discord(self, ctx: commands.Context) -> None:
        """
        Sub command of socials that sends only our discord invite.

        !socials discord
        """
        await ctx.send("discord.gg/...")


"""
Set up subscription database, using OAuth tokens as necessary
"""
async def setup_database(db: asqlite.Pool) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:

    # Create our token table, if it doesn't exist
    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Fetch any existing tokens
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == BOT_ID:
                continue

            subs.extend(
                [
                    eventsub.ChatMessageSubscription(broadcaster_user_id=row["user_id"], user_id=BOT_ID),
                    eventsub.ChannelPollBeginSubscription(broadcaster_user_id=row["user_id"]),
                    eventsub.ChannelBitsUseSubscription(broadcaster_user_id=row["user_id"]),
                    eventsub.ChannelSubscribeSubscription(broadcaster_user_id=row["user_id"]),
                    eventsub.ChannelSubscriptionGiftSubscription(broadcaster_user_id=row["user_id"]),
                    eventsub.ChannelSubscribeMessageSubscription(broadcaster_user_id=row["user_id"]),
                ]
            )

    return tokens, subs

"""
Perform final bot initilization, then send to asyncio runner
"""
def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb:
            tokens, subs = await setup_database(tdb)

            async with Bot(token_database=tdb, subs=subs) as bot:
                for pair in tokens:
                    await bot.add_token(*pair)

                await bot.start(load_tokens=False)

    # test donation interface
    print(f"----- STARTUP DONATION -----")
    sheet.donationToRow("TwitchIO", "1.99", "Test Donation", "TwitchIO startup test")
    print(f"----- STARTUP DONATION -----")

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt")


if __name__ == "__main__":
    main()
