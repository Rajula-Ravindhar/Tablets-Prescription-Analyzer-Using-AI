import os
import urllib.parse
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image
from dotenv import find_dotenv, load_dotenv

# 1. Initialization & Configuration
_ = load_dotenv(find_dotenv())
API_KEY = os.getenv("geminiapi_key")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-2.5-flash"

# 2.Generates the  Map Link from Coordinates
def get_map_link_url(location_data):
    """
    Takes location data (dict) from frontend and returns a Google Maps URL.
    """
    if location_data and location_data.get('latitude') and location_data.get('longitude'):
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        search_query = "nearbymedicalshops"
        encoded_query = urllib.parse.quote(search_query)
        return f"https://www.google.com/maps/search/{encoded_query}/@{latitude},{longitude},15z"
    return "Location not provided or permission denied."

# 3.System Prompt
def get_system_prompt(map_link_url):
    return f'''
    You are an expert-level Medical Data Extraction tool. Your primary function is to analyze images of medical prescriptions and extract key information in a highly structured, machine-readable format.

    ## Your Task
    1. Perform OCR on all provided handwritten and printed text.
    2. Identify and extract key medical entities.
    3. **Ensure that no two medication entries are identical.**
    4. Include timings (e.g., 'after meals') within the frequency column.
    5. Extract the Quantity of medicines (ex : 10 tablets )
    5. Add this link to the `Map_link` column for every entry: {map_link_url}
    6. Fetch the patient details as patient_info compulsory, if not found return 'not provided'
    7. Importantly : only i want this columns : 'medications','Dosage','Frequency','duration','Quantity','Map_link' and 
        in patient_info the columns are : 'Name','Age','Date'.

    ## Output Format
    You MUST return your findings in a strict json format only.

    
    The json structure must be:
    'patient_info and prescription data separate dictionaries in nested with other dictionary.
    
    
    ## Critical Guardrails
    * You are NOT a doctor. Do not provide medical advice.
    * If the image is blurry, return "Error: Image is unreadable".
    * If a field is missing, use "Not provided".
    '''

# 4. Main Logic: Image Processing & API Calling.
def analyze_prescription(image_file, location_data):
    
    try:
        # A. Prepare Image
        image = Image.open(image_file)
        max_width = 1024
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)

        # B. Prepare Context (Map & Prompt)
        map_url = get_map_link_url(location_data)
        system_prompt = get_system_prompt(map_url)

        # C. Call Model
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=system_prompt
        )
        
        # Return the stream generator
        return model.generate_content(image, stream=True)

    except Exception as e:
        raise e
    
def analyze_for_warnings(model_data):
    #api calling
    Api_key=os.getenv('Gemini_api_key')
    genai.configure(api_key=Api_key)
    SYSTEM_PROMPT=f"""
    You are an expert Medical Safety Analyst. Your task is to analyze a list of transcribed medications and
      provide critical safety information. 
    
    The user is providing the full transcribed text from a patient prescription.
    
    ## Primary Task
    1. Scan the text for all 'Drug Name', 'Dosage', and 'Duration' entries.
    2. Identify and list any potential drug-drug interactions (DDI) based on the combinations found.
    3. Identify any medications with known severe side effects (Black Box Warnings, etc.) or high dependency risk.
    4. Flag any unusually high dosages or durations compared to standard therapeutic guidelines.
    5. **Crucially:** If the provided text mentions a drug name is 'N/A' or if the dosage/duration is incomplete, flag the drug and request clarity.
    ## Input Text to Analyze
    ---
    {model_data}
    ---
    
    ## Output Format
    You MUST return a simple, clean list of warnings or findings. Do not include any conversational text. 
    If there are no issues, simply return: 'No critical safety issues found based on the extracted data.'
    
    Format each warning clearly:
    - [INTERACTION]: Drug A + Drug B: Risk of Severe Hypotension.
    - [DOSAGE ISSUE]: Amoxicillin: Dosage of 2000mg/day is unusually high. Review required.
    - [SIDE EFFECT]: Drug X: Monitor for increased risk of liver toxicity.
    - [DATA GAP]: Drug Y: Dosage is missing (N/A). Cannot confirm safety profile.
    
    """
    Model=genai.GenerativeModel(model_name=MODEL_NAME,system_instruction=SYSTEM_PROMPT)
    return Model.generate_content('ANALYZE THE ABOVE DATA',stream=True)