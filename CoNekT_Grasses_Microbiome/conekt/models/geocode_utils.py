import requests
from urllib.parse import urlencode

def geocode_location(country, local=None):
    base_url = "https://nominatim.openstreetmap.org/search?"
    headers = {'User-Agent': 'genome-geolocation-app'}

    # 1. Tentar geocodificar usando o local (se disponível)
    if local:
        query = f"{local}, {country}"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1
        }
        response = requests.get(base_url + urlencode(params), headers=headers)
        
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            lat = float(data['lat'])
            lon = float(data['lon'])
            print(f"Geocoding successful for {local}, {country}: {lat}, {lon}")
            return lat, lon
        else:
            print(f"Geocoding failed for {local}. Trying with country only...")

    # 2. Se a geocodificação do local falhar ou não existir, tentar com o país
    params = {
        'q': country,
        'format': 'json',
        'limit': 1
    }
    response = requests.get(base_url + urlencode(params), headers=headers)
    
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        lat = float(data['lat'])
        lon = float(data['lon'])
        print(f"Geocoding successful for {country}: {lat}, {lon}")
        return lat, lon
    else:
        print(f"Geocoding failed for {country}. No coordinates found.")
        return None, None  # Retorna None se não encontrar as coordenadas
