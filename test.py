import requests

username = "kunuwako"  # Replace with a valid username
BASE_URL = "https://api.chess.com/pub"
HEADERS = {"User-Agent": "Chess-in-Kenya (Contact: wakokunu@gmail.com)"}

stats_url = f"{BASE_URL}/player/{username}/stats"
response = requests.get(stats_url, headers=HEADERS, timeout=10)
print(response.json())  # Print the full response
