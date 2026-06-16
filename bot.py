import asyncio
import os
import json
import aiohttp
import feedparser
from datetime import datetime, timezone
from TikTokLive import TikTokLiveClient

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
TIKTOK_USERNAME = os.environ["TIKTOK_USERNAME"]
STATE_FILE = "live_state.json"


def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"is_live": False, "last_post_id": None}


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


async def check_new_post(state: dict) -> dict:
    feed_url = f"https://rsshub-24wb.onrender.com/tiktok/user/@{TIKTOK_USERNAME}"

    async with aiohttp.ClientSession() as session:
        async with session.get(feed_url) as resp:
            if resp.status != 200:
                print(f"RSS feed error: {resp.status}")
                return state
            content = await resp.text()

    feed = feedparser.parse(content)

    if not feed.entries:
        print("No posts found in RSS feed.")
        return state

    latest = feed.entries[0]
    latest_id = latest.get("id") or latest.get("link")
    latest_title = latest.get("title", "New TikTok post")
    latest_link = latest.get("link", f"https://www.tiktok.com/@{TIKTOK_USERNAME}")

    last_post_id = state.get("last_post_id")

    if latest_id != last_post_id:
        print(f"New post detected: {latest_id}")

        embed = {
            "title": f"📱 {TIKTOK_USERNAME} just posted on TikTok!",
            "description": f"**{latest_title}**\n🔗 [Watch here]({latest_link})",
            "color": 65280  # green
        }
        await send_discord_message(f"📣 **{TIKTOK_USERNAME}** just uploaded a new TikTok!", embed)
        state["last_post_id"] = latest_id
    else:
        print("No new posts.")

    return state


async def main():
    state = read_state()

    # --- Check if live ---
    was_live = state.get("is_live", False)

    client = TikTokLiveClient(unique_id=f"@{TIKTOK_USERNAME}")
    currently_live = await client.is_live()

    print(f"@{TIKTOK_USERNAME} — was_live={was_live}, currently_live={currently_live}")

    if currently_live and not was_live:
        embed = {
            "title": f"🔴 {TIKTOK_USERNAME} is LIVE on TikTok!",
            "description": f"Jump in now!\n🔗 [Watch here](https://www.tiktok.com/@{TIKTOK_USERNAME}/live)",
            "color": 16711680  # red
        }
        await send_discord_message("@everyone 📣 Your favorite streamer just went live!", embed)
        state["is_live"] = True

    elif not currently_live and was_live:
        await send_discord_message(f"📴 **{TIKTOK_USERNAME}** has ended their TikTok Live. Thanks for watching!")
        state["is_live"] = False

    else:
        print("No live state change.")

    # --- Check for new posts ---
    state = await check_new_post(state)

    # --- Save state ---
    write_state(state)


asyncio.run(main())
