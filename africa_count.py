import requests
import pandas as pd
import time
import logging

# Configure logging
logging.basicConfig(
    filename="african_player_fetch.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# List of African countries with ISO alpha-2 codes, ISO alpha-3 codes, and full names
african_countries = [
    {"alpha2": "DZ", "alpha3": "DZA", "name": "Algeria"},
    {"alpha2": "AO", "alpha3": "AGO", "name": "Angola"},
    {"alpha2": "BJ", "alpha3": "BEN", "name": "Benin"},
    {"alpha2": "BW", "alpha3": "BWA", "name": "Botswana"},
    {"alpha2": "BF", "alpha3": "BFA", "name": "Burkina Faso"},
    {"alpha2": "BI", "alpha3": "BDI", "name": "Burundi"},
    {"alpha2": "CM", "alpha3": "CMR", "name": "Cameroon"},
    {"alpha2": "CV", "alpha3": "CPV", "name": "Cabo Verde"},
    {"alpha2": "CF", "alpha3": "CAF", "name": "Central African Republic"},
    {"alpha2": "TD", "alpha3": "TCD", "name": "Chad"},
    {"alpha2": "KM", "alpha3": "COM", "name": "Comoros"},
    {"alpha2": "CG", "alpha3": "COG", "name": "Congo"},
    {"alpha2": "CD", "alpha3": "COD", "name": "Congo (DRC)"},
    {"alpha2": "CI", "alpha3": "CIV", "name": "Côte d'Ivoire"},
    {"alpha2": "DJ", "alpha3": "DJI", "name": "Djibouti"},
    {"alpha2": "EG", "alpha3": "EGY", "name": "Egypt"},
    {"alpha2": "GQ", "alpha3": "GNQ", "name": "Equatorial Guinea"},
    {"alpha2": "ER", "alpha3": "ERI", "name": "Eritrea"},
    {"alpha2": "SZ", "alpha3": "SWZ", "name": "Eswatini"},
    {"alpha2": "ET", "alpha3": "ETH", "name": "Ethiopia"},
    {"alpha2": "GA", "alpha3": "GAB", "name": "Gabon"},
    {"alpha2": "GM", "alpha3": "GMB", "name": "Gambia"},
    {"alpha2": "GH", "alpha3": "GHA", "name": "Ghana"},
    {"alpha2": "GN", "alpha3": "GIN", "name": "Guinea"},
    {"alpha2": "GW", "alpha3": "GNB", "name": "Guinea-Bissau"},
    {"alpha2": "KE", "alpha3": "KEN", "name": "Kenya"},
    {"alpha2": "LS", "alpha3": "LSO", "name": "Lesotho"},
    {"alpha2": "LR", "alpha3": "LBR", "name": "Liberia"},
    {"alpha2": "LY", "alpha3": "LBY", "name": "Libya"},
    {"alpha2": "MG", "alpha3": "MDG", "name": "Madagascar"},
    {"alpha2": "MW", "alpha3": "MWI", "name": "Malawi"},
    {"alpha2": "ML", "alpha3": "MLI", "name": "Mali"},
    {"alpha2": "MR", "alpha3": "MRT", "name": "Mauritania"},
    {"alpha2": "MU", "alpha3": "MUS", "name": "Mauritius"},
    {"alpha2": "MA", "alpha3": "MAR", "name": "Morocco"},
    {"alpha2": "MZ", "alpha3": "MOZ", "name": "Mozambique"},
    {"alpha2": "NA", "alpha3": "NAM", "name": "Namibia"},
    {"alpha2": "NE", "alpha3": "NER", "name": "Niger"},
    {"alpha2": "NG", "alpha3": "NGA", "name": "Nigeria"},
    {"alpha2": "RW", "alpha3": "RWA", "name": "Rwanda"},
    {"alpha2": "ST", "alpha3": "STP", "name": "Sao Tome and Principe"},
    {"alpha2": "SN", "alpha3": "SEN", "name": "Senegal"},
    {"alpha2": "SC", "alpha3": "SYC", "name": "Seychelles"},
    {"alpha2": "SL", "alpha3": "SLE", "name": "Sierra Leone"},
    {"alpha2": "SO", "alpha3": "SOM", "name": "Somalia"},
    {"alpha2": "ZA", "alpha3": "ZAF", "name": "South Africa"},
    {"alpha2": "SS", "alpha3": "SSD", "name": "South Sudan"},
    {"alpha2": "SD", "alpha3": "SDN", "name": "Sudan"},
    {"alpha2": "TZ", "alpha3": "TZA", "name": "Tanzania"},
    {"alpha2": "TG", "alpha3": "TGO", "name": "Togo"},
    {"alpha2": "TN", "alpha3": "TUN", "name": "Tunisia"},
    {"alpha2": "UG", "alpha3": "UGA", "name": "Uganda"},
    {"alpha2": "ZM", "alpha3": "ZMB", "name": "Zambia"},
    {"alpha2": "ZW", "alpha3": "ZWE", "name": "Zimbabwe"}
]

# Chess.com API base URL
BASE_URL = "https://api.chess.com/pub/country"
HEADERS = {"User-Agent": "ChessAfricaHeatmap (contact: wakokunu@gmail.com)"}

# Dictionary to store player counts
country_player_counts = []

# Fetch players for each country
for country in african_countries:
    try:
        country_code = country["alpha2"]
        url = f"{BASE_URL}/{country_code}/players"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise error for bad responses
        players = response.json().get("players", [])
        country_player_counts.append({
            "Country Code": country_code,
            "ISO-3": country["alpha3"],
            "Country Name": country["name"],
            "Player Count": len(players)
        })
        logging.info(f"Fetched {len(players)} players for {country['name']} ({country_code}).")
    except Exception as e:
        logging.error(f"Error fetching data for {country['name']} ({country_code}): {e}")
        country_player_counts.append({
            "Country Code": country_code,
            "ISO-3": country["alpha3"],
            "Country Name": country["name"],
            "Player Count": None  # Mark as unavailable
        })
    time.sleep(1)  # Respect API rate limits

# Convert to DataFrame
country_df = pd.DataFrame(country_player_counts)

# Save to CSV
output_file = "african_country_player_counts.csv"
try:
    country_df.to_csv(output_file, index=False)
    logging.info(f"Player counts saved to {output_file}")
except Exception as e:
    logging.error(f"Error saving player counts to CSV: {e}")
