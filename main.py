from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI4NTRlMmFiMC1kNmYyLTAxM2QtZDhhOS0xZWRhMTNiOWEyZmYiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzQwNjMxMDY4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6InNlYXJjaGluZy1yZWNvIn0.s6rzKU3YAhO5CLoUqkHwKn1ldtni4mZy5oSNQIoxBRo"
PLATFORM = "steam"
PLAYER_NAMES = ["whaleandseal", "BestnameSE", "239_xxx", "HEELU_"]

def get_player_id(player_name):
    url = f"https://api.pubg.com/shards/{PLATFORM}/players?filter[playerNames]={player_name}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/vnd.api+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data'][0]['id']
    return None

def get_current_season():
    url = f"https://api.pubg.com/shards/{PLATFORM}/seasons"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/vnd.api+json"
    }
    response = requests.get(url, headers=headers)
    seasons = response.json()['data']
    current = next(season for season in seasons if season['attributes']['isCurrentSeason'])
    return current['id']

def get_player_stats(player_id, season_id):
    url = f"https://api.pubg.com/shards/{PLATFORM}/players/{player_id}/seasons/{season_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/vnd.api+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def calculate_average_damage(stats_data):
    stats = stats_data['data']['attributes']['gameModeStats'].get('squad', {})
    damage = stats.get('damageDealt', 0)
    games = stats.get('roundsPlayed', 0)
    return damage / games if games > 0 else 0

@app.get("/", response_class=HTMLResponse)
async def show_stats(request: Request):
    current_season = get_current_season()
    results = []

    for name in PLAYER_NAMES:
        player_id = get_player_id(name)
        if player_id:
            stats = get_player_stats(player_id, current_season)
            if stats:
                avg_dmg = calculate_average_damage(stats)
                results.append((name, avg_dmg))

    results.sort(key=lambda x: x[1], reverse=True)

    # 4명 딜량을 문자열로 만듦 (예: whaleandseal(123.45), ...)
    og_description = ", ".join([f"{name}({dmg:.2f})" for name, dmg in results])
    og_description = f"배그 딜량 순위: {og_description}"

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "results": results,
        "og_description": og_description
    })
