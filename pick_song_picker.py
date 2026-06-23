import asyncio
import os
import json
import random
import aiohttp
from datetime import date

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_GUILD_ID = os.environ["DISCORD_GUILD_ID"]
STATE_FILE = "live_state.json"


def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"is_live": False}


def write_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


async def fetch_guild_members():
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    url = f"https://discord.com/api/v10/guilds/{DISCORD_GUILD_ID}/members?limit=1000"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Discord API error {resp.status}: {text}")
            return await resp.json()


async def send_discord_message(content: str, embed: dict = None):
    payload = {"content": content}
    if embed:
        payload["embeds"] = [embed]
    async with aiohttp.ClientSession() as session:
        async with session.post(WEBHOOK_URL, json=payload) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                raise Exception(f"Webhook error {resp.status}: {text}")


async def main():
    today = str(date.today())
    state = read_state()

    if state.get("last_picker_date") == today:
        print(f"Already picked today ({today}). Skipping.")
        return

    members = await fetch_guild_members()
    humans = [m for m in members if not m["user"].get("bot", False)]

    if not humans:
        raise Exception("No human members found in server.")

    chosen = random.choice(humans)
    user = chosen["user"]
    mention = f"<@{user['id']}>"
    display_name = chosen.get("nick") or user.get("global_name") or user["username"]

    embed = {
        "title": "🎵 Today's First Song Picker!",
        "description": (
            f"{mention} has been chosen to pick the **first song** of today's stream!\n\n"
            "Stream starts at **5:45pm** — get your request ready! 🎶"
        ),
        "color": 5814783,
    }
    await send_discord_message("@everyone 🎶 Today's song picker has been chosen!", embed)

    state["last_picker_date"] = today
    state["last_picker_id"] = user["id"]
    state["last_picker_name"] = display_name
    write_state(state)
    print(f"Picked: {display_name} ({user['id']})")


asyncio.run(main())
