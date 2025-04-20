from os import path, environ
from sqlalchemy import func
from base64 import b64decode, b64encode
from threading import Thread
from bs4 import BeautifulSoup
from traceback import print_exc
from requests import get as rget
from flask_sqlalchemy import SQLAlchemy
from verboselogs import VerboseLogger, VERBOSE
from coloredlogs import install as Cloginstall
from flask import Flask, render_template, request, jsonify, send_from_directory
import json, requests
from time import sleep
from dotenv import load_dotenv, dotenv_values
from flask_cors import CORS
import google.auth
import google.auth.transport.requests



#Initialize Logger
logger = VerboseLogger('APP')
Cloginstall(level=VERBOSE, fmt='[%(asctime)s] | [%(name)s] | %(levelname)-8s | %(message)s')


load_dotenv('config.env', override=True)

GOOGLE_MAPS_API_KEY = environ.get('GOOGLE_MAPS_API_KEY', '')
GEMINI_API_KEY = environ.get('GEMINI_API_KEY', '')

if len(GOOGLE_MAPS_API_KEY) == 0:
    logger.error("GOOGLE_MAPS_API_KEY not found! Exiting...")
    exit(1)

ENDPOINT = environ.get('ENDPOINT', '')
ENDPOINT_ID = environ.get('ENDPOINT_ID', '')
PROJECT_ID = environ.get('PROJECT_ID', '')
LOCATION = environ.get('LOCATION', '')


#Initialize Flask
app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization"]}})
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = ''

#Initialize Database
db = SQLAlchemy(app)

# Table Movies
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), primary_key=False, nullable=True)

    def __repr__(self) -> str:
        return f"{self.id} | {self.name}"

def google_credentials():
    credentials, project_id = google.auth.load_credentials_from_file('./default_access_credentials.json', scopes=['https://www.googleapis.com/auth/cloud-platform'])
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    access_token = credentials.token
    print(access_token)
    return access_token



class LocalInfo():
    def __init__(self, lat, lon) -> None:
        self.lat = lat
        self.lon = lon
    
    def weather(self):
        url = f"https://weather.googleapis.com/v1/currentConditions:lookup?key={GOOGLE_MAPS_API_KEY}&location.latitude={self.lat}&location.longitude={self.lon}"
        response = requests.get(url)
        print(response.text)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching weather data: {response.status_code}")
            return None

    def air_quality(self):
        body = {
        "location": {
            "latitude": self.lat,
            "longitude": self.lon
        }
        }
        url = f"https://airquality.googleapis.com/v1/currentConditions:lookup?key={GOOGLE_MAPS_API_KEY}"
        response = requests.post(url, json=body)
        print(response.text)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching air quality data: {response.status_code}")
            return None
        
    def pollen(self):
        url = f"https://pollen.googleapis.com/v1/forecast:lookup?key={GOOGLE_MAPS_API_KEY}&location.latitude={self.lat}&location.longitude={self.lon}&days=1"
        response = requests.get(url)
        print(response.text)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching weather data: {response.status_code}")
            return None

class DiseaseVision():
    def __init__(self, endpoint, endpoint_id, project_id, location, auth) -> None:
        self.endpoint_url = f"https://{endpoint}/v1/projects/{project_id}/locations/{location}/endpoints/{endpoint_id}:predict"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key="
        self.auth_bearer = auth

    def disease_vision(self, label):
        labels = {
            "Apple___apple_scab": {
                "plant": "apple",
                "disease": "apple scab"
            },
            "Apple___black_rot": {
                "plant": "apple",
                "disease": "black rot"
            },
            "Apple___cedar_apple_rust": {
                "plant": "apple",
                "disease": "cedar apple rust"
            },
            "Apple___healthy": {
                "plant": "apple",
                "disease": "healthy"
            },
            "Blueberry___healthy": {
                "plant": "blueberry",
                "disease": "healthy"
            },
            "Cherry___healthy": {
                "plant": "cherry",
                "disease": "healthy"
            },
            "Cherry___powdery_mildew": {
                "plant": "cherry",
                "disease": "powdery mildew"
            },
            "Grape___black_rot": {
                "plant": "grape",
                "disease": "black rot"
            },
            "Grape___esca_black_measles": {
                "plant": "grape",
                "disease": "esca black measles"
            },
            "Grape___healthy": {
                "plant": "grape",
                "disease": "healthy"
            },
            "Grape___leaf_blight_isariopsis_leaf_spot": {
                "plant": "grape",
                "disease": "leaf blight isariopsis leaf spot"
            },
            "Orange___haunglongbing_citrus_greening": {
                "plant": "orange",
                "disease": "haunglongbing citrus greening"
            },
            "Peach___bacterial_spot": {
                "plant": "peach",
                "disease": "bacterial spot"
            },
            "Peach___healthy": {
                "plant": "peach",
                "disease": "healthy"
            },
            "Pepper_bell___bacterial_spot": {
                "plant": "pepper_bell",
                "disease": "bacterial spot"
            },
            "Pepper_bell___healthy": {
                "plant": "pepper_bell",
                "disease": "healthy"
            },
            "Potato___early_blight": {
                "plant": "potato",
                "disease": "early blight"
            },
            "Potato___healthy": {
                "plant": "potato",
                "disease": "healthy"
            },
            "Potato___late_blight": {
                "plant": "potato",
                "disease": "late blight"
            },
            "Raspberry___healthy": {
                "plant": "raspberry",
                "disease": "healthy"
            },
            "Rice___bacterial_leaf_blight": {
                "plant": "rice",
                "disease": "bacterial leaf blight"
            },
            "Rice___brown_spot": {
                "plant": "rice",
                "disease": "brown spot"
            },
            "Rice___healthy": {
                "plant": "rice",
                "disease": "healthy"
            },
            "Rice___leaf_blast": {
                "plant": "rice",
                "disease": "leaf blast"
            },
            "Rice___leaf_scald": {
                "plant": "rice",
                "disease": "leaf scald"
            },
            "Rice___narrow_brown_spot": {
                "plant": "rice",
                "disease": "narrow brown spot"
            },
            "Rice___neck_blast": {
                "plant": "rice",
                "disease": "neck blast"
            },
            "Rice___rice_hispa": {
                "plant": "rice",
                "disease": "rice hispa"
            },
            "Rice___sheath_blight": {
                "plant": "rice",
                "disease": "sheath blight"
            },
            "Rice___tungro": {
                "plant": "rice",
                "disease": "tungro"
            },
            "Soybean___healthy": {
                "plant": "soybean",
                "disease": "healthy"
            },
            "Squash___powdery_mildew": {
                "plant": "squash",
                "disease": "powdery mildew"
            },
            "Strawberry___healthy": {
                "plant": "strawberry",
                "disease": "healthy"
            },
            "Strawberry___leaf_scorch": {
                "plant": "strawberry",
                "disease": "leaf scorch"
            },
            "Tomato___bacterial_spot": {
                "plant": "tomato",
                "disease": "bacterial spot"
            },
            "Tomato___early_blight": {
                "plant": "tomato",
                "disease": "early blight"
            },
            "Tomato___healthy": {
                "plant": "tomato",
                "disease": "healthy"
            },
            "Tomato___late_blight": {
                "plant": "tomato",
                "disease": "late blight"
            },
            "Tomato___leaf_mold": {
                "plant": "tomato",
                "disease": "leaf mold"
            },
            "Tomato___mosaic_virus": {
                "plant": "tomato",
                "disease": "mosaic virus"
            },
            "Tomato___septoria_leaf_spot": {
                "plant": "tomato",
                "disease": "septoria leaf spot"
            },
            "Tomato___spider_mites_two_spotted_spider_mite": {
                "plant": "tomato",
                "disease": "spider mites two spotted spider mite"
            },
            "Tomato___target_spot": {
                "plant": "tomato",
                "disease": "target spot"
            },
            "Tomato___yellow_leaf_curl_virus": {
                "plant": "tomato",
                "disease": "yellow leaf curl virus"
            }
        }

        for l in labels:
            if l in label:
                plant = labels[l]["plant"]
                disease = labels[l]["disease"]
                return plant, disease
        return "", ""



    def classify(self, image):
        filename = "image.png"
        
        body = {
            "instances": [
                    {
                        "key": filename,
                        "image_bytes": {
                        "b64": image
                        }
                    }
                ],
            "parameters": {
                "confidenceThreshold": 0.5, 
                "maxPredictions": 1}
            }
        
        headers = {
            "Authorization": f"Bearer {self.auth_bearer}",
            "Content-Type": "application/json"
            }
        
        response = requests.post(
            self.endpoint_url, 
            headers=headers, 
            data=json.dumps(body)
            )
        
        response = response.json()

        labeled_score = {}
        if "predictions" not in response:
            self.auth_bearer = google_credentials()
            
            response = requests.post(
            self.endpoint_url, 
            headers=headers, 
            data=json.dumps(body)
            )
            response = response.json()
            if "predictions" not in response:
                predictions = []
        else:
            predictions = response["predictions"]
        for prediction in predictions:
            key = prediction["key"]
            labels = prediction["labels"]
            scores = prediction["scores"]
            for label, score in zip(labels, scores):
                raw_bytes = b64decode(label)
                label = raw_bytes.decode('utf-8', errors='ignore')
                labeled_score[label] = score

        highest_score = 0
        highest_label =""
        for label, score in labeled_score.items():
            if score > highest_score:
                highest_score = score
                highest_label = label
            
        plant, disease = self.disease_vision(highest_label)

        predict = {
            "plant": plant,
            "disease": disease,
            "confidence": highest_score,
        }

        return predict
    
    def info(self, plant, disease):

        prompt = (
            f"give me response for,\n"
            f"plant: {plant}, disease: {disease}\n"
            f"in json format\n\n"
            f"{{\n"
            f'  "plant_complete_name": "", #plant complete name\n'
            f'  "disease_name": "", #disease if any, if healthy then Healthy\n'
            f'  "disease_type": "", #disease type if any, if healthy then ""\n'
            f'  "description_information": "", ## description of plant\'s disease if disease otherwise plants description if healthy\n'
            f'  "symptoms": [\n'
            f'  ], ## symptoms if disease otherwise empty if healthy\n'
            f'  "cure_pesticides": [\n'
            f'    {{\n'
            f'      "type": "", # type\n'
            f'      "details": "", # details\n'
            f'      "examples": [\n'
            f'      ], # examples\n'
            f'      "notes": "" # if extra notes\n'
            f'      \n'
            f'    }},... #multiple pesticides or cures for the particular disease, otherwise give general pesticides if healthy\n'
            f'  ],\n'
            f'  "preventions": [\n'
            f'    {{\n'
            f'      "category": "", #category\n'
            f'      "methods": [\n'
            f'      ] #methods\n'
            f'    }},... #how to prevent the disease if any or general preventions\n'
            f'  ],\n'
            f'  "more_info_note": "" #extra more info note \n'
            f'}}\n\n'
            f"Return the response as a standard JSON object directly.\n"
            f"Do NOT include any introductory text, explanations, markdown formatting (like ```json), or any wrapping structure.\n"
            f"The output should ONLY be the JSON object itself. For example:\n"
            f'{{"plant_complete_name": "Tomato", "disease_name":"...", ...}}'
        )
        body = {
            "contents": [{
                "parts":[{"text": prompt}]
                }]
            }
        
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(f"{self.gemini_url}{GEMINI_API_KEY}", headers=headers, json=body)

        source = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        content = source.strip().strip('```json').strip('```').strip()

        respones = json.loads(content)
        return respones

class LocalMarket():
    def __init__(self, key: str) -> None:
        self.api_key = key
        self.place_type = "market"
        self.keywords = "mandi OR APMC OR CCI OR farmers market OR vegetable market OR fruit market OR dairy OR cotton market"
        self.place_details_fields = "name,formatted_address,formatted_phone_number,opening_hours,website,business_status,types,geometry"
        self.nearby_search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.place_details_url ="https://maps.googleapis.com/maps/api/place/details/json"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key="
        

    def get_local_market(self, lat, lon, radius):
        all_results = []
        params = {
            'location': f"{lat},{lon}",
            'radius': radius,
            'type': self.place_type,
            'keyword': self.keywords,
            'key': self.api_key,
            'language': 'en-IN'
        }
        page_num = 1

        while True:
            print(page_num)
            if page_num == 1:
                current_params = params
            else:
                current_params = {
                    'pagetoken': next_page_token,
                    'key': self.api_key
                }
                sleep(2)
            print(params)

            try:
                response = requests.get(self.nearby_search_url, params=current_params, timeout=15)
                response.raise_for_status()
                results_data = response.json()
                print(results_data)
                status = results_data.get('status')

                if status == 'OK':
                    page_results = results_data.get('results', [])
                    all_results.extend(page_results)

                    next_page_token = results_data.get('next_page_token')
                    if next_page_token and len(all_results) < 60:
                        page_num += 1
                    else:
                        break
                
                elif status == 'ZERO_RESULTS':
                    return None

                elif status == 'INVALID_REQUEST':
                    logger.error(f"Invalid request on Nearby Search API for page {page_num}.")
                    return None

                else:
                    logger.error(f"Error on Nearby Search API for page {page_num}: {status}")
                    return None

            except requests.exceptions.Timeout:
                logger.error(f"Timeout occurred during Nearby Search API request for page {page_num}.")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error during Nearby Search API request for page {page_num}: {e}")
                return None
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON response from Nearby Search API for page {page_num}.")
                return None
            except Exception as e:
                logger.error(f"An unexpected error occurred during search on page {page_num}: {e}")
                return None
        return all_results
        

    def get_place_details(self, place_id):
        params = {
            'place_id': place_id,
            'fields': self.place_details_fields,
            'key': self.api_key,
            'language': 'en-IN'
        }

        try:
            response = requests.get(self.place_details_url, params=params, timeout=10)
            response.raise_for_status()
            details_data = response.json()

            status = details_data.get('status')
            if status == 'OK':
                return details_data.get('result', {})
            else:
                error_msg = details_data.get('error_message', 'No specific error message provided.')
                logger.error(f"Error fetching details for place_id {place_id}: API Status '{status}'. Message: {error_msg}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Place Details API request for place_id {place_id}: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON response from Place Details API for place_id {place_id}.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during details fetch for {place_id}: {e}")
            return None
        

    def search(self, lat, lon, radius):
        logger.verbose(f"Searching for local markets: {lat}, {lon} | Radius: {radius} m")
        markets = []
        results = self.get_local_market(lat, lon, radius)

        if results is not None:
            found_count = 0
            processed_ids = set()

            for i, place in enumerate(results):
                place_id = place.get('place_id')
                place_name = place.get('name', 'N/A')

                details = self.get_place_details(place_id)
                processed_ids.add(place_id)

                if details:
                    market = {}
                    found_count += 1
                    market["name"] = details.get('name', 'N/A')
                    market["address"] = details.get('formatted_address', 'N/A')
                    market["phone"] = details.get('formatted_phone_number', 'N/A')
                    market["website"] = details.get('website', 'N/A')
                    market["status"] = details.get('business_status', 'N/A')
                    markets.append(market)
        
        prompt = (
            f"Analyze the following list of potential market places: {json.dumps(markets)}. "
            "Filter this list to include ONLY places that are highly relevant to farmers for buying/selling/trading agricultural produce "
            "(like APMC, Mandi, specific commodity markets like cotton/vegetable/fruit markets, or dedicated farmer's markets). "
            "Exclude general stores, supermarkets, individual shops, or places not primarily focused on agricultural trade. "
            "Return the filtered list as a standard JSON array (a list of dictionaries) directly. "
            "Do NOT include any introductory text, explanations, markdown formatting (like ```json), or any wrapping structure. "
            "The output should ONLY be the JSON array itself. For example: "
            '[{"name": "APMC Example", "address": "...", ...}, {"name": "XYZ Fruit Market", ...}]'
            " If no places match the criteria, return an empty JSON array []."
        )
        body = {
            "contents": [{
                "parts":[{"text": prompt}]
                }]
            }
        
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(f"{self.gemini_url}{GEMINI_API_KEY}", headers=headers, json=body)

        source = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        content = source.strip().strip('```json').strip('```').strip()

        respones = json.loads(content)

        return {"results": respones, "count": len(markets)}


def crops_search(crop):
    print(crop)
    prompt = (
        f"Provide detailed information for the crop: {crop}. "
        "Format the response strictly as a JSON object with the following structure:\n"
        "{\n"
        f'  "crop": "{crop}",\n' # Placeholder for the actual crop name confirmed by the model
        '  "image_url": "URL_to_representative_image",\n'
        '  "name": "Common Name (Scientific Name)",\n'
        '  "description": "Detailed description of the crop.",\n'
        '  "farming_techniques": [\n'
        '    "Technique 1 description",\n'
        '    "Technique 2 description",\n'
        '    "..."\n'
        '  ],\n'
        '  "fertilizers": {\n'
        '    "recommended_doses": "General NPK recommendations or specific advice.",\n'
        '    "application_timing": "When to apply fertilizers (e.g., planting, vegetative stage).",\n'
        '    "organic_fertilizers": "Examples of suitable organic options (e.g., compost, manure)." \n'
        '  },\n'
        '  "extra_info": {\n'
        '    "water_required": "General water needs (e.g., high, moderate, low) or specific amount.",\n'
        '    "temperature": {\n'
        '      "ideal_range": "Ideal temperature range (e.g., 20-30°C).",\n'
        '      "minimum": "Minimum survival temperature.",\n'
        '      "maximum": "Maximum tolerance temperature."\n'
        '    },\n'
        '    "humidity": {\n'
        '      "ideal_range": "Ideal relative humidity range (e.g., 60-80%)."\n'
        '    },\n'
        '    "soil_type": "Preferred soil types (e.g., sandy loam, clay).",\n'
        '    "season": "Primary growing season(s) (e.g., Kharif, Rabi, Summer).",\n'
        '    "growth_duration": "Typical time from planting to harvest (e.g., 90-120 days).",\n'
        '    "yield": "Expected yield per unit area (e.g., tonnes/hectare).",\n'
        '    "nutritional_value": "Key nutritional highlights (e.g., Rich in Vitamin C, source of fiber)." \n'
        '  }\n'
        '}\n\n'
        "Return the response as a standard JSON object directly.\n"
        "Do NOT include any introductory text, explanations, markdown formatting (like ```json), or any wrapping structure.\n"
        "The output should ONLY be the JSON object itself. Ensure the 'crop' field in the JSON matches the requested crop or its most common name."
        f" If no information is found for '{crop}', return a JSON object like: {{\"error\": \"Crop not found\"}}."
    ) # Use format to insert the crop name into the structure example

    body = {
        "contents": [{
            "parts":[{"text": prompt}]
            }]
        }
    
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}", headers=headers, json=body)

    source = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    content = source.strip().strip('```json').strip('```').strip()

    respones = json.loads(content)

    return {"results": respones}






CDD = DiseaseVision(ENDPOINT, ENDPOINT_ID, PROJECT_ID, LOCATION, google_credentials())

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/v1/image-classification', methods=["POST"])
def image_classification():
    logger.info("Image received for classification.")
    data = request.json
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({"error": "No image provided"}), 400
    try:
        image_bytes = b64decode(image_b64)
    except Exception as e:
        return jsonify({"error": "Invalid base64 image data"}), 400
    
    classified = CDD.classify(image_b64)
    if classified["confidence"] < 0.3:
        classified["success"] = False
    else:
        classified["success"] = True
        info = CDD.info(classified["plant"], classified["disease"])
        classified["info"] = info

    return jsonify(classified)


@app.route('/api/v1/local-market', methods=["POST"])
def local_market():
    print("Local market search request received")
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    radius = data.get('radius')

    if not lat or not lon or not radius:
        return jsonify({"error": "Invalid input"}), 400

    local_market = LocalMarket(GOOGLE_MAPS_API_KEY)
    markets = local_market.search(lat, lon, radius)
    
    return jsonify(markets)


@app.route('/api/v1/environment', methods=["POST"])
def environment():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    environment = LocalInfo(lat, lon)
    weather = environment.weather()
    temp = weather["temperature"]["degrees"]
    cond = weather["weatherCondition"]["description"]["text"]
    precipitate = weather["precipitation"]["probability"]["percent"]
    qpf = weather["precipitation"]["qpf"]["quantity"]
    air_quality = environment.air_quality()
    aqi = air_quality["indexes"][0]["aqi"]
    cat = air_quality["indexes"][0]["category"]
    info = {
        "temperature": {"temperature": temp, "conditions": cond},
        "air_quality": {"air_quality": aqi, "category": cat},
        "precipitate": {"precipitate": precipitate, "qpf": qpf}
    }
    print(info)
    return jsonify(info)


@app.route('/api/v1/crops-list')
def crops_list():
    crops = {
    "crops": [
        {"id": 1, "name": "Wheat", "image": "https://www.shutterstock.com/image-photo/golden-wheat-field-ears-close-260nw-2469161609.jpg"},
        {"id": 2, "name": "Rice", "image": "https://www.shutterstock.com/image-photo/rice-grains-abundant-fertile-yellow-600nw-2433181629.jpg"},
        {"id": 3, "name": "Corn", "image": "https://www.shutterstock.com/image-photo/closeup-corn-cobs-plantation-field-260nw-2192611413.jpg"},
        {"id": 4, "name": "Soybean", "image": "https://www.shutterstock.com/image-photo/soybean-pods-plantationin-sunny-day-260nw-2458171115.jpg"},
        {"id": 5, "name": "Potato", "image": "https://www.shutterstock.com/image-photo/pile-ripe-potatoes-on-ground-260nw-1509459776.jpg"},
        {"id": 6, "name": "Sugarcane", "image": "https://www.shutterstock.com/image-photo/sugarcane-fields-worlds-largest-crop-260nw-2500391331.jpg"},
        {"id": 7, "name": "Cotton", "image": "https://www.shutterstock.com/image-photo/cotton-ready-harvest-260nw-1087595693.jpg"},
        {"id": 8, "name": "Barley", "image": "https://www.shutterstock.com/image-photo/gold-wheat-field-idea-rich-600nw-2481039185.jpg"},
        {"id": 9, "name": "Cassava", "image": "https://m.media-amazon.com/images/I/61V017ctz9L.AC_UF1000,1000_QL80.jpg"},
        {"id": 10, "name": "Tomato", "image": "https://www.shutterstock.com/image-photo/ripe-tomato-plant-growing-greenhouse-260nw-1729065064.jpg"},
        {"id": 11, "name": "Banana", "image": "https://www.shutterstock.com/image-photo/green-bananas-growing-on-trees-600nw-2376822797.jpg"},
        {"id": 12, "name": "Sweetcorn", "image": "https://www.shutterstock.com/image-photo/closeup-corn-cobs-plantation-field-600nw-2312934759.jpg"},
        {"id": 13, "name": "Sweet Potato", "image": "https://www.shutterstock.com/image-photo/harvesting-organic-sweet-potatoes-summer-260nw-2255569603.jpg"},
        {"id": 14, "name": "Grape", "image": "https://www.shutterstock.com/image-photo/ripe-chardonnay-grapes-hanging-on-600nw-2504739555.jpg"},
        {"id": 15, "name": "Orange", "image": "https://www.shutterstock.com/image-photo/orange-garden-ripe-oranges-on-600nw-2482486845.jpg"},
        {"id": 16, "name": "Apple", "image": "https://www.shutterstock.com/image-photo/red-apples-on-apple-tree-600nw-61300474.jpg"},
        {"id": 17, "name": "Mango", "image": "https://www.greenlife.co.ke/wp-content/uploads/2022/04/Mangoes.jpg"},
        {"id": 18, "name": "Lemon", "image": "https://www.shutterstock.com/image-photo/lemon-on-tree-spain-how-260nw-1528446326.jpg"},
        {"id": 19, "name": "Onion", "image": "https://www.shutterstock.com/image-photo/sprouts-onion-close-background-260nw-1704135319.jpg"},
        {"id": 20, "name": "Garlic", "image": "https://www.thespruce.com/thmb/Ptvalllc9czYhXZuq2_hF6_YIyk=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/hardneck-and-softneck-garlic-2540056-02-187d9130324346319f9d2df16a7124c5.jpg"},
        {"id": 21, "name": "Cabbage", "image": "https://www.shutterstock.com/image-photo/young-cabbage-grows-farmer-field-600nw-2117937080.jpg"},
        {"id": 22, "name": "Carrot", "image": "https://www.shutterstock.com/image-photo/fresh-kitchen-garden-carrots-on-600nw-154184855.jpg"},
        {"id": 23, "name": "Peanut", "image": "https://www.shutterstock.com/image-photo/fresh-peanuts-plants-roots-harvest-260nw-2462156121.jpg"},
        {"id": 24, "name": "Oat", "image": "https://www.shutterstock.com/image-photo/oatmeal-flakes-oat-ears-background-260nw-1589223256.jpg"},
        {"id": 25, "name": "Rye", "image": "https://www.shutterstock.com/shutterstock/photos/494852617/display_1500/stock-photo-the-rye-crop-or-rye-cultural-lat-secale-cereale-494852617.jpg"},
        {"id": 26, "name": "Sorghum", "image": "https://www.shutterstock.com/shutterstock/photos/131971589/display_1500/stock-photo-mature-sorghum-131971589.jpg"},
        {"id": 27, "name": "Millet", "image": "https://www.shutterstock.com/image-photo/ripe-millet-crops-fields-260nw-764055478.jpg"},
        {"id": 28, "name": "Canola", "image": "https://www.shutterstock.com/image-photo/canola-crop-growing-on-vast-260nw-2508352739.jpg"},
        {"id": 29, "name": "Sunflower", "image": "https://www.shutterstock.com/image-photo/large-happy-sunflower-oil-crop-260nw-261244847.jpg"},
        {"id": 30, "name": "Palm Oil", "image": "https://www.shutterstock.com/image-photo/palm-oil-plantation-growing-up-260nw-2025523610.jpg"},
        {"id": 31, "name": "Coconut", "image": "https://www.shutterstock.com/shutterstock/photos/2279211797/display_1500/stock-photo-low-angle-view-of-a-coconut-tree-with-bunches-of-yellow-coconut-fruits-in-miami-florida-view-of-a-2279211797.jpg"},
        {"id": 32, "name": "Olive", "image": "https://www.shutterstock.com/image-photo/olive-tree-branch-young-green-260nw-2468821339.jpg"},
        {"id": 33, "name": "Rapeseed", "image": "https://www.shutterstock.com/image-photo/detail-flowering-rapeseed-canola-colza-260nw-1006641043.jpg"},
        {"id": 34, "name": "Mustard", "image": "https://www.shutterstock.com/image-photo/yellow-blossoming-mustards-flowers-mustard-260nw-2583664123.jpg"},
        {"id": 35, "name": "Sesame", "image": "https://www.shutterstock.com/shutterstock/photos/2492066143/display_1500/stock-photo-sesame-seed-on-tree-in-the-field-stock-photo-sesame-agriculture-branch-plant-part-bush-tree-2492066143.jpg"},
        {"id": 36, "name": "Linseed", "image": "https://www.shutterstock.com/image-photo/flax-common-linseed-flowers-linum-260nw-1179552307.jpg"},
        {"id": 37, "name": "Bean", "image": "https://www.shutterstock.com/image-photo/mung-bean-pods-fruits-elongated-260nw-2177316941.jpg"},
        {"id": 38, "name": "Pea", "image": "https://www.shutterstock.com/image-photo/green-peas-260nw-305361377.jpg"},
        {"id": 39, "name": "Lentil", "image": "https://www.shutterstock.com/image-photo/closeup-lentil-plant-white-flowers-260nw-1397559449.jpg"},
        {"id": 40, "name": "Chickpea", "image": "https://t4.ftcdn.net/jpg/02/77/58/17/360_F_277581792_trTRdyvnE9H5rPLt1WDLUyHK7ZJ8FAny.jpg"},
        {"id": 41, "name": "Pigeonpea", "image": "https://www.shutterstock.com/shutterstock/photos/2450805981/display_1500/stock-photo-pigeon-pea-gude-kacang-gude-kacang-kayo-kacang-bali-cajanus-cajan-red-gram-tur-pwa-kongo-2450805981.jpg"},
        {"id": 42, "name": "Cowpea", "image": "https://www.shutterstock.com/image-photo/cowpea-plants-growth-vegetable-garden-260nw-2506662263.jpg"},
        {"id": 43, "name": "Kidney Bean", "image": "https://www.shutterstock.com/image-photo/ripe-pods-kidney-bean-growing-260nw-2305939497.jpg"},
        {"id": 44, "name": "Lima Bean", "image": "https://www.shutterstock.com/image-photo/fresh-green-lima-bean-called-260nw-2227333907.jpg"},
        {"id": 45, "name": "Navy Bean", "image": "https://www.shutterstock.com/image-photo/unripe-bean-phaseolus-vulgaris-pods-260nw-409555957.jpg"},
        {"id": 46, "name": "Black Bean", "image": "https://www.shutterstock.com/image-photo/black-bean-blooming-garden-farm-600nw-1930322486.jpg"},
        {"id": 47, "name": "Mung Bean", "image": "https://www.shutterstock.com/shutterstock/photos/2177316941/display_1500/stock-photo-mung-bean-pods-the-fruits-are-elongated-cylindrical-or-flat-cylindrical-pods-crop-planting-at-the-2177316941.jpg"},
        {"id": 48, "name": "Broad Bean", "image": "https://www.shutterstock.com/image-photo/broad-bean-plant-field-vegetable-260nw-2301758387.jpg"},
        {"id": 49, "name": "Lettuce", "image": "https://www.shutterstock.com/image-photo/field-green-lettuce-vegetables-260nw-1439327225.jpg"},
        {"id": 50, "name": "Spinach", "image": "https://www.shutterstock.com/image-photo/growing-spinach-home-garden-260nw-2493717821.jpg"},
        {"id": 51, "name": "Broccoli", "image": "https://www.shutterstock.com/image-photo/broccoli-plant-flowers-green-leaves-600nw-2405843075.jpg"},
        {"id": 52, "name": "Cauliflower", "image": "https://www.shutterstock.com/image-photo/cauliflower-vegetable-planting-crop-full-260nw-1010784172.jpg"},
        {"id": 53, "name": "Bell Pepper", "image": "https://www.shutterstock.com/image-photo/bell-pepper-garden-600nw-732301561.jpg"},
        {"id": 54, "name": "Chili Pepper", "image": "https://www.shutterstock.com/shutterstock/photos/2496906343/display_1500/stock-photo-red-chili-peppers-and-two-red-chilies-plants-in-the-garden-2496906343.jpg"},
        {"id": 55, "name": "Cucumber", "image": "https://www.shutterstock.com/image-photo/growth-flowering-greenhouse-cucumbers-growing-600nw-2017673318.jpg"},
        {"id": 56, "name": "Eggplant", "image": "https://www.shutterstock.com/image-photo/eggplant-plant-growing-community-garden-260nw-1919679422.jpg"},
        {"id": 57, "name": "Zucchini", "image": "https://www.shutterstock.com/shutterstock/photos/2496861281/display_1500/stock-photo-growing-zucchini-in-a-home-garden-2496861281.jpg"},
        {"id": 58, "name": "Pumpkin", "image": "https://www.shutterstock.com/image-photo/pumpkins-field-260nw-218941237.jpg"},
        {"id": 59, "name": "Watermelon", "image": "https://www.shutterstock.com/image-photo/watermelon-cultivation-greenhouse-almeria-260nw-1959090841.jpg"},
        {"id": 60, "name": "Melon", "image": "https://www.shutterstock.com/image-photo/closeup-cantaloupes-growing-farmland-yunlin-260nw-2383446731.jpg"},
        {"id": 61, "name": "Pineapple", "image": "https://www.shutterstock.com/image-photo/pineapple-trees-that-currently-bearing-260nw-1728162277.jpg"},
        {"id": 62, "name": "Strawberry", "image": "https://www.shutterstock.com/image-photo/strawberry-plant-stawberry-bush-strawberries-260nw-1012028083.jpg"},
        {"id": 63, "name": "Blueberry", "image": "https://www.shutterstock.com/image-photo/closeup-duke-variety-blueberry-bushes-600nw-2489541263.jpg"},
        {"id": 64, "name": "Raspberry", "image": "https://www.shutterstock.com/image-photo/branch-ripe-raspberries-garden-260nw-1063904021.jpg"},
        {"id": 65, "name": "Blackberry", "image": "https://www.shutterstock.com/image-photo/blackberries-grow-garden-ripe-unripe-600nw-1915946041.jpg"},
        {"id": 66, "name": "Cherry", "image": "https://www.theenglishgarden.co.uk/_gatsby/file/f5db0684c8e5bbac3eb26682c2829eb2/29303_shutterstock_91347101.jpg"},
        {"id": 67, "name": "Peach", "image": "https://www.shutterstock.com/image-photo/fresh-ripe-peaches-on-tree-260nw-2504314787.jpg"},
        {"id": 68, "name": "Plum", "image": "https://www.shutterstock.com/image-photo/ripe-red-plum-first-crop-260nw-708315175.jpg"},
        {"id": 69, "name": "Apricot", "image": "https://media.istockphoto.com/id/1159599400/photo/a-bunch-of-ripe-apricots-branch-in-sunlight.jpg?s=612x612&w=0&k=20&c=SWFeOSglMFm7nxAul67ois7Wn-0kMQms-RZ64O4OUNk="},
        {"id": 70, "name": "Pear", "image": "https://www.shutterstock.com/image-photo/branch-ripe-organic-cultivar-pears-600nw-2135841129.jpg"},
        {"id": 71, "name": "Avocado", "image": "https://www.shutterstock.com/image-photo/avocados-fruit-avocado-trees-plantations-600nw-2465925437.jpg"},
        {"id": 72, "name": "Kiwi", "image": "https://t3.ftcdn.net/jpg/10/85/13/22/360_F_1085132299_ajGVJdxpeJNBoCretx0yjnIzVHjlRQna.jpg"},
        {"id": 73, "name": "Fig", "image": "https://www.shutterstock.com/image-photo/branch-fig-tree-ficus-carica-600nw-1486047620.jpg"},
        {"id": 74, "name": "Date", "image": "https://www.shutterstock.com/image-photo/date-palm-green-dates-fresh-600w-1470733832.jpg"},
        {"id": 75, "name": "Grapefruit", "image": "https://www.shutterstock.com/shutterstock/photos/663995491/display_1500/stock-photo-grapefruit-citrus-fruit-tree-leaves-summer-tropics-useful-diet-vitamins-garden-grow-663995491.jpg"},
        {"id": 76, "name": "Lime", "image": "https://www.shutterstock.com/image-photo/lemon-hanging-on-tree-260nw-113382538.jpg"},
        {"id": 77, "name": "Papaya", "image": "https://www.shutterstock.com/image-photo/big-orange-papaya-gree-tree-600nw-2489304241.jpg"},
        {"id": 78, "name": "Guava", "image": "https://www.shutterstock.com/image-photo/three-guava-on-tree-branch-260nw-1868808538.jpg"},
        {"id": 79, "name": "Pomegranate", "image": "https://www.shutterstock.com/image-photo/pomegranate-on-tree-branch-red-260nw-2194349587.jpg"},
        {"id": 80, "name": "Artichoke", "image": "https://www.shutterstock.com/shutterstock/photos/1994091137/display_1500/stock-photo-five-beautiful-artichokes-on-a-plant-surrounded-by-a-vegetable-garden-harvest-from-an-organic-and-1994091137.jpg"},
        {"id": 81, "name": "Asparagus", "image": "https://www.shutterstock.com/image-photo/asparagus-fresh-pickled-green-bunches-600nw-1673452201.jpg"},
        {"id": 82, "name": "Beetroot", "image": "https://www.shutterstock.com/image-photo/beetroot-plant-fresh-grows-garden-600nw-2517701777.jpg"},
        {"id": 83, "name": "Brussels Sprout", "image": "https://www.shutterstock.com/image-photo/brussel-sprouts-on-farm-600w-175194545.jpg"},
        {"id": 84, "name": "Celery", "image": "https://www.shutterstock.com/image-photo/crop-ripe-celery-stacked-on-600nw-1798086349.jpg"},
        {"id": 85, "name": "Collard Greens", "image": "https://www.shutterstock.com/image-photo/collard-greens-large-green-leaves-600nw-2325292777.jpg"},
        {"id": 86, "name": "Kale", "image": "https://www.shutterstock.com/image-photo/green-kale-leaves-garden-260nw-2519028769.jpg"},
        {"id": 87, "name": "Leek", "image": "https://www.shutterstock.com/shutterstock/photos/2494046285/display_1500/stock-photo-leek-plants-varieties-choosing-the-best-types-for-your-garden-2494046285.jpg"},
        {"id": 88, "name": "Okra", "image": "https://www.shutterstock.com/shutterstock/photos/752656450/display_1500/stock-photo-okra-crop-in-fruiting-stage-752656450.jpg"},
        {"id": 89, "name": "Radish", "image": "https://www.shutterstock.com/image-photo/daikon-white-radish-on-garden-600w-2492415699.jpg"},
        {"id": 90, "name": "Rhubarb", "image": "https://www.shutterstock.com/shutterstock/photos/2406099359/display_1500/stock-photo-common-rhubarb-rheum-rhabarbarum-rhubarb-2406099359.jpg"},
        {"id": 91, "name": "Turnip", "image": "https://www.shutterstock.com/shutterstock/photos/2485738745/display_1500/stock-photo-a-close-up-of-fresh-purple-and-white-turnips-perfect-for-healthy-eating-cooking-and-farming-2485738745.jpg"},
        {"id": 92, "name": "Yam", "image": "https://www.shutterstock.com/shutterstock/photos/728209285/display_1500/stock-photo-sweet-potatoes-yams-harvesting-organic-sweet-potatoes-gardening-sweet-potatoes-growing-728209285.jpg"},
        {"id": 93, "name": "Ginger", "image": "https://www.shutterstock.com/shutterstock/photos/1926066902/display_1500/stock-photo-harvest-ginger-in-the-garden-1926066902.jpg"},
        {"id": 94, "name": "Turmeric", "image": "https://www.shutterstock.com/image-photo/harvest-turmeric-morning-260nw-1910753563.jpg"},
        {"id": 95, "name": "Cinnamon", "image": "https://www.shutterstock.com/image-photo/whole-spice-cinnamon-powdered-shelf-600nw-2510042917.jpg"},
        {"id": 96, "name": "Clove", "image": "https://rukminim2.flixcart.com/image/850/1000/xif0q/plant-sapling/m/p/g/no-annual-yes-labongo-masla-plants-small-1-grow-bag-corofitam-original-imahyzfgpcx2rsrr.jpeg?q=20&crop=false"},
        {"id": 97, "name": "Nutmeg", "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_jGuU0BhTx7ZpIPewVEhpWMUOtrImNOsw1w&s"}
    ]
}
    return jsonify(crops)
    


@app.route('/api/v1/crop-info', methods=["POST"])
def crops():
    data = request.json
    plant = data.get('crop')
    if not plant:
        return jsonify({"error": "Invalid input"}), 400
    else:
        info = crops_search(plant)
        return jsonify(info)
    


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)