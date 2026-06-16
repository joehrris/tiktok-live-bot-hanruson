import asyncio
import os
import json
import aiohttp
from TikTokLive import TikTokLiveClient

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
TIKTOK_USERNAME = os.environ["TIKTOK_USERNAME"]
STATE_FILE = "live_state.json"


def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"is_live": False}


def write_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


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
    state = read_state()
    was_live = state.get("is_live", False)

    client = TikTokLiveClient(unique_id=f"@{TIKTOK_USERNAME}")
    currently_live = await client.is_live()

    print(f"@{TIKTOK_USERNAME} — was_live={was_live}, currently_live={currently_live}")

    if currently_live and not was_live:
        embed = {
            "title": f"🔴 {TIKTOK_USERNAME} is LIVE on TikTok!",
            "description": f"Jump in now!\n🔗 [Watch here](https://www.tiktok.com/@{TIKTOK_USERNAME}/live)",
            "color": 16711680
        }
        await send_discord_message("@everyone 📣 Your favorite streamer just went live!", embed)
        write_state({"is_live": True})

    elif not currently_live and was_live:
        await send_discord_message(f"📴 **{TIKTOK_USERNAME}** has ended their TikTok Live. Thanks for watching!")
        write_state({"is_live": False})

    else:
        print("No state change. Nothing to post.")


asyncio.run(main())
