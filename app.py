import json
import os
import time

import requests

from flask import (
    Flask,
    Response,
    jsonify,
    render_template_string,
    request,
    stream_with_context,
)

app = Flask(__name__)

# ============================================================
# RAIDHARA CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

MODEL = os.environ.get("RAIDHARA_MODEL", "qwen2.5:3b")

# Set to -1 to keep the model loaded until Ollama is restarted.
KEEP_ALIVE = -1

# Keep this reasonably small for a laptop with 16 GB RAM.
NUM_CTX = 2048
NUM_PREDICT = 180

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ta": "Tamil",
    "mr": "Marathi",
}

# ============================================================
# DEMONSTRATION DATA
# ============================================================
# These examples are NOT live prices or live weather.
# Replace them with verified API/database results before
# presenting them as real-world information.
# ============================================================

WEATHER_DEMO = [
    {
        "city": "Bengaluru",
        "temperature": 25,
        "condition": "Partly cloudy",
    },
    {
        "city": "Mangaluru",
        "temperature": 30,
        "condition": "Humid",
    },
    {
        "city": "Mysuru",
        "temperature": 27,
        "condition": "Cloudy",
    },
    {
        "city": "Hubballi",
        "temperature": 29,
        "condition": "Mostly sunny",
    },
]

FERTILIZER_SHOPS_DEMO = [
    {
        "shop": "GreenField Agro Centre",
        "city": "Bengaluru",
        "product": "Urea",
        "pack": "45 kg bag",
        "price": 266.50,
    },
    {
        "shop": "Sri Lakshmi Fertilizers",
        "city": "Bengaluru",
        "product": "NPK 19:19:19",
        "pack": "1 kg pack",
        "price": 180.00,
    },
    {
        "shop": "Coastal Krishi Stores",
        "city": "Mangaluru",
        "product": "Neem cake",
        "pack": "5 kg pack",
        "price": 250.00,
    },
    {
        "shop": "Mysuru Agro Solutions",
        "city": "Mysuru",
        "product": "Vermicompost",
        "pack": "5 kg bag",
        "price": 150.00,
    },
]


# ============================================================
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {
    "en": {
        "brand": "RAIDHARA",
        "tagline": "Your intelligent farming companion",
        "greeting": "Hello, how can I help you?",
        "listening": "LISTENING...",
        "thinking": "RAIDHARA IS THINKING...",
        "speak": "TAP TO SPEAK",
        "stop": "STOP LISTENING",
        "ask_placeholder": "Ask RAIDHARA anything about farming...",
        "send": "ASK RAIDHARA",
        "weather": "WEATHER",
        "market": "MARKET",
        "crops": "CROP HEALTH",
        "support": "SUPPORT",
        "weather_title": "Weather Forecast",
        "fertilizer_title": "Nearby Fertilizer Prices",
        "water_title": "Water Calculator",
        "health_title": "Crop Health Check",
        "soil_title": "Soil & Crop Planning",
        "schemes_title": "Government Schemes",
        "city": "City",
        "product": "Fertilizer",
        "search": "SEARCH",
        "area": "Farm area in acres",
        "depth": "Water depth in millimetres",
        "calculate": "CALCULATE WATER",
        "crop": "Crop",
        "symptoms": "Describe the symptoms",
        "soil_ph": "Soil pH, if known",
        "soil_type": "Soil type",
        "submit": "ANALYSE",
        "schemes_desc": "Explore official agricultural scheme portals.",
        "demo": "DEMO DATA — NOT LIVE OR VERIFIED",
        "water_result": "Estimated water required",
        "litres": "litres",
        "answer": "RAIDHARA RESPONSE",
        "loading": "Processing your request...",
        "empty": "Please enter a question.",
        "error": "Something went wrong.",
        "all": "All",
        "price": "Example price",
        "shop": "Shop",
        "pack": "Pack",
        "condition": "Condition",
        "temperature": "Temperature",
        "not_live": "Demonstration values only. Live data is not connected.",
        "select_language": "Language",
        "health_hint": "Describe the crop, affected leaves, and how long symptoms have been present.",
        "soil_hint": "Example: Tomato, loamy soil, pH 6.5",
        "water_hint": "Enter the area and irrigation depth.",
        "no_shops": "No example shops match this search.",
        "official": "Open official portal",
        "water_note": "This is a volume calculation, not a crop-specific irrigation recommendation.",
    },

    "hi": {
        "brand": "RAIDHARA",
        "tagline": "आपका बुद्धिमान कृषि सहायक",
        "greeting": "नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ?",
        "listening": "सुन रहा हूँ...",
        "thinking": "RAIDHARA सोच रहा है...",
        "speak": "बोलने के लिए दबाएँ",
        "stop": "सुनना बंद करें",
        "ask_placeholder": "खेती के बारे में RAIDHARA से पूछें...",
        "send": "RAIDHARA से पूछें",
        "weather": "मौसम",
        "market": "बाज़ार",
        "crops": "फसल स्वास्थ्य",
        "support": "सहायता",
        "weather_title": "मौसम पूर्वानुमान",
        "fertilizer_title": "आसपास खाद की कीमतें",
        "water_title": "पानी की गणना",
        "health_title": "फसल स्वास्थ्य जाँच",
        "soil_title": "मिट्टी और फसल योजना",
        "schemes_title": "सरकारी योजनाएँ",
        "city": "शहर",
        "product": "खाद",
        "search": "खोजें",
        "area": "खेत का क्षेत्रफल (एकड़)",
        "depth": "पानी की गहराई (मिलीमीटर)",
        "calculate": "पानी की गणना करें",
        "crop": "फसल",
        "symptoms": "लक्षण बताएँ",
        "soil_ph": "मिट्टी का pH, यदि ज्ञात हो",
        "soil_type": "मिट्टी का प्रकार",
        "submit": "विश्लेषण करें",
        "schemes_desc": "आधिकारिक कृषि योजना पोर्टल देखें।",
        "demo": "डेमो डेटा — लाइव या सत्यापित नहीं",
        "water_result": "अनुमानित पानी की आवश्यकता",
        "litres": "लीटर",
        "answer": "RAIDHARA का उत्तर",
        "loading": "आपके प्रश्न पर काम हो रहा है...",
        "empty": "कृपया प्रश्न लिखें।",
        "error": "कुछ गलत हुआ।",
        "all": "सभी",
        "price": "उदाहरण कीमत",
        "shop": "दुकान",
        "pack": "पैक",
        "condition": "स्थिति",
        "temperature": "तापमान",
        "not_live": "केवल उदाहरण। लाइव डेटा जुड़ा नहीं है।",
        "select_language": "भाषा",
        "health_hint": "फसल, प्रभावित पत्तियों और लक्षणों की अवधि बताएँ।",
        "soil_hint": "उदाहरण: टमाटर, दोमट मिट्टी, pH 6.5",
        "water_hint": "क्षेत्रफल और पानी की गहराई भरें।",
        "no_shops": "इस खोज से मेल खाती उदाहरण दुकान नहीं मिली।",
        "official": "आधिकारिक पोर्टल खोलें",
        "water_note": "यह पानी की मात्रा की गणना है, फसल-विशिष्ट सिंचाई सलाह नहीं।",
    },

    "te": {
        "brand": "RAIDHARA",
        "tagline": "మీ తెలివైన వ్యవసాయ సహాయకుడు",
        "greeting": "నమస్కారం, నేను మీకు ఎలా సహాయపడగలను?",
        "listening": "వింటున్నాను...",
        "thinking": "RAIDHARA ఆలోచిస్తోంది...",
        "speak": "మాట్లాడటానికి నొక్కండి",
        "stop": "వినడం ఆపండి",
        "ask_placeholder": "వ్యవసాయం గురించి RAIDHARAని అడగండి...",
        "send": "RAIDHARAని అడగండి",
        "weather": "వాతావరణం",
        "market": "మార్కెట్",
        "crops": "పంట ఆరోగ్యం",
        "support": "సహాయం",
        "weather_title": "వాతావరణ అంచనా",
        "fertilizer_title": "దగ్గరలో ఎరువుల ధరలు",
        "water_title": "నీటి లెక్కింపు",
        "health_title": "పంట ఆరోగ్య పరిశీలన",
        "soil_title": "నేల మరియు పంట ప్రణాళిక",
        "schemes_title": "ప్రభుత్వ పథకాలు",
        "city": "నగరం",
        "product": "ఎరువు",
        "search": "వెతకండి",
        "area": "పొలం విస్తీర్ణం (ఎకరాలు)",
        "depth": "నీటి లోతు (మిల్లీమీటర్లు)",
        "calculate": "నీటిని లెక్కించండి",
        "crop": "పంట",
        "symptoms": "లక్షణాలను వివరించండి",
        "soil_ph": "నేల pH, తెలిసి ఉంటే",
        "soil_type": "నేల రకం",
        "submit": "విశ్లేషించండి",
        "schemes_desc": "అధికారిక వ్యవసాయ పథకాల వెబ్‌సైట్లను చూడండి.",
        "demo": "డెమో డేటా — ప్రత్యక్ష లేదా ధృవీకరించిన సమాచారం కాదు",
        "water_result": "అంచనా నీటి అవసరం",
        "litres": "లీటర్లు",
        "answer": "RAIDHARA సమాధానం",
        "loading": "మీ ప్రశ్నను పరిశీలిస్తున్నాం...",
        "empty": "దయచేసి ప్రశ్న నమోదు చేయండి.",
        "error": "ఏదో సమస్య వచ్చింది.",
        "all": "అన్నీ",
        "price": "ఉదాహరణ ధర",
        "shop": "దుకాణం",
        "pack": "ప్యాక్",
        "condition": "స్థితి",
        "temperature": "ఉష్ణోగ్రత",
        "not_live": "ఉదాహరణలు మాత్రమే. ప్రత్యక్ష డేటా అనుసంధానం లేదు.",
        "select_language": "భాష",
        "health_hint": "పంట, ప్రభావిత ఆకులు, లక్షణాలు ఎప్పటి నుంచి ఉన్నాయో వివరించండి.",
        "soil_hint": "ఉదాహరణ: టమాటా, లోమీ నేల, pH 6.5",
        "water_hint": "విస్తీర్ణం మరియు నీటి లోతు నమోదు చేయండి.",
        "no_shops": "ఈ శోధనకు సరిపోయే దుకాణాలు లేవు.",
        "official": "అధికారిక వెబ్‌సైట్ తెరవండి",
        "water_note": "ఇది నీటి పరిమాణ లెక్క మాత్రమే; పంటకు ప్రత్యేకమైన నీటిపారుదల సలహా కాదు.",
    },

    "kn": {
        "brand": "RAIDHARA",
        "tagline": "ನಿಮ್ಮ ಬುದ್ಧಿವಂತ ಕೃಷಿ ಸಹಾಯಕ",
        "greeting": "ನಮಸ್ಕಾರ, ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        "listening": "ಕೇಳುತ್ತಿದ್ದೇನೆ...",
        "thinking": "RAIDHARA ಯೋಚಿಸುತ್ತಿದೆ...",
        "speak": "ಮಾತನಾಡಲು ಒತ್ತಿರಿ",
        "stop": "ಕೇಳುವುದನ್ನು ನಿಲ್ಲಿಸಿ",
        "ask_placeholder": "ಕೃಷಿಯ ಬಗ್ಗೆ RAIDHARA ಅನ್ನು ಕೇಳಿ...",
        "send": "RAIDHARA ಅನ್ನು ಕೇಳಿ",
        "weather": "ಹವಾಮಾನ",
        "market": "ಮಾರುಕಟ್ಟೆ",
        "crops": "ಬೆಳೆ ಆರೋಗ್ಯ",
        "support": "ಸಹಾಯ",
        "weather_title": "ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ",
        "fertilizer_title": "ಹತ್ತಿರದ ರಸಗೊಬ್ಬರ ಬೆಲೆಗಳು",
        "water_title": "ನೀರಿನ ಲೆಕ್ಕಾಚಾರ",
        "health_title": "ಬೆಳೆ ಆರೋಗ್ಯ ಪರಿಶೀಲನೆ",
        "soil_title": "ಮಣ್ಣು ಮತ್ತು ಬೆಳೆ ಯೋಜನೆ",
        "schemes_title": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು",
        "city": "ನಗರ",
        "product": "ರಸಗೊಬ್ಬರ",
        "search": "ಹುಡುಕಿ",
        "area": "ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಎಕರೆ)",
        "depth": "ನೀರಿನ ಆಳ (ಮಿಲಿಮೀಟರ್)",
        "calculate": "ನೀರನ್ನು ಲೆಕ್ಕಿಸಿ",
        "crop": "ಬೆಳೆ",
        "symptoms": "ಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ",
        "soil_ph": "ಮಣ್ಣಿನ pH, ತಿಳಿದಿದ್ದರೆ",
        "soil_type": "ಮಣ್ಣಿನ ಪ್ರಕಾರ",
        "submit": "ವಿಶ್ಲೇಷಿಸಿ",
        "schemes_desc": "ಅಧಿಕೃತ ಕೃಷಿ ಯೋಜನೆಗಳ ಪೋರ್ಟಲ್‌ಗಳನ್ನು ನೋಡಿ.",
        "demo": "ಡೆಮೊ ಮಾಹಿತಿ — ನೇರ ಅಥವಾ ಪರಿಶೀಲಿಸಿದ ಮಾಹಿತಿ ಅಲ್ಲ",
        "water_result": "ಅಂದಾಜು ನೀರಿನ ಅವಶ್ಯಕತೆ",
        "litres": "ಲೀಟರ್",
        "answer": "RAIDHARA ಉತ್ತರ",
        "loading": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
        "empty": "ದಯವಿಟ್ಟು ಪ್ರಶ್ನೆ ನಮೂದಿಸಿ.",
        "error": "ಏನೋ ತಪ್ಪಾಗಿದೆ.",
        "all": "ಎಲ್ಲವೂ",
        "price": "ಉದಾಹರಣೆ ಬೆಲೆ",
        "shop": "ಅಂಗಡಿ",
        "pack": "ಪ್ಯಾಕ್",
        "condition": "ಸ್ಥಿತಿ",
        "temperature": "ತಾಪಮಾನ",
        "not_live": "ಉದಾಹರಣೆಗಳು ಮಾತ್ರ. ನೇರ ಮಾಹಿತಿ ಸಂಪರ್ಕಗೊಂಡಿಲ್ಲ.",
        "select_language": "ಭಾಷೆ",
        "health_hint": "ಬೆಳೆ, ಬಾಧಿತ ಎಲೆಗಳು ಮತ್ತು ಲಕ್ಷಣಗಳ ಅವಧಿಯನ್ನು ವಿವರಿಸಿ.",
        "soil_hint": "ಉದಾಹರಣೆ: ಟೊಮೇಟೊ, ಲೋಮಿ ಮಣ್ಣು, pH 6.5",
        "water_hint": "ವಿಸ್ತೀರ್ಣ ಮತ್ತು ನೀರಿನ ಆಳವನ್ನು ನಮೂದಿಸಿ.",
        "no_shops": "ಈ ಹುಡುಕಾಟಕ್ಕೆ ಹೊಂದುವ ಅಂಗಡಿಗಳಿಲ್ಲ.",
        "official": "ಅಧಿಕೃತ ಪೋರ್ಟಲ್ ತೆರೆಯಿರಿ",
        "water_note": "ಇದು ನೀರಿನ ಪ್ರಮಾಣದ ಲೆಕ್ಕಾಚಾರ ಮಾತ್ರ; ಬೆಳೆ-ನಿರ್ದಿಷ್ಟ ನೀರಾವರಿ ಸಲಹೆಯಲ್ಲ.",
    },

    "ta": {
        "brand": "RAIDHARA",
        "tagline": "உங்கள் அறிவார்ந்த விவசாய உதவியாளர்",
        "greeting": "வணக்கம், நான் உங்களுக்கு எப்படி உதவலாம்?",
        "listening": "கேட்கிறேன்...",
        "thinking": "RAIDHARA யோசிக்கிறது...",
        "speak": "பேச அழுத்தவும்",
        "stop": "கேட்பதை நிறுத்தவும்",
        "ask_placeholder": "விவசாயம் பற்றி RAIDHARA-விடம் கேளுங்கள்...",
        "send": "RAIDHARA-விடம் கேளுங்கள்",
        "weather": "வானிலை",
        "market": "சந்தை",
        "crops": "பயிர் ஆரோக்கியம்",
        "support": "உதவி",
        "weather_title": "வானிலை முன்னறிவிப்பு",
        "fertilizer_title": "அருகிலுள்ள உர விலைகள்",
        "water_title": "நீர் கணக்கீடு",
        "health_title": "பயிர் ஆரோக்கியச் சோதனை",
        "soil_title": "மண் மற்றும் பயிர் திட்டமிடல்",
        "schemes_title": "அரசுத் திட்டங்கள்",
        "city": "நகரம்",
        "product": "உரம்",
        "search": "தேடுக",
        "area": "நிலப்பரப்பு (ஏக்கர்)",
        "depth": "நீர் ஆழம் (மில்லிமீட்டர்)",
        "calculate": "நீரைக் கணக்கிடுக",
        "crop": "பயிர்",
        "symptoms": "அறிகுறிகளை விவரிக்கவும்",
        "soil_ph": "மண்ணின் pH, தெரிந்தால்",
        "soil_type": "மண் வகை",
        "submit": "பகுப்பாய்வு செய்க",
        "schemes_desc": "அதிகாரப்பூர்வ வேளாண் திட்ட இணையதளங்களைப் பாருங்கள்.",
        "demo": "மாதிரி தரவு — நேரடி அல்லது சரிபார்க்கப்பட்டதல்ல",
        "water_result": "மதிப்பிடப்பட்ட நீர் தேவை",
        "litres": "லிட்டர்",
        "answer": "RAIDHARA பதில்",
        "loading": "உங்கள் கேள்வி செயலாக்கப்படுகிறது...",
        "empty": "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்.",
        "error": "ஏதோ தவறு ஏற்பட்டது.",
        "all": "அனைத்தும்",
        "price": "மாதிரி விலை",
        "shop": "கடை",
        "pack": "பொதி",
        "condition": "நிலை",
        "temperature": "வெப்பநிலை",
        "not_live": "மாதிரிகள் மட்டுமே. நேரடி தரவு இணைக்கப்படவில்லை.",
        "select_language": "மொழி",
        "health_hint": "பயிர், பாதிக்கப்பட்ட இலைகள் மற்றும் அறிகுறிகளின் காலத்தை விவரிக்கவும்.",
        "soil_hint": "எடுத்துக்காட்டு: தக்காளி, வண்டல் மண், pH 6.5",
        "water_hint": "பரப்பளவு மற்றும் நீரின் ஆழத்தை உள்ளிடவும்.",
        "no_shops": "இந்தத் தேடலுக்கு பொருந்தும் கடைகள் இல்லை.",
        "official": "அதிகாரப்பூர்வ தளத்தைத் திறக்கவும்",
        "water_note": "இது நீரின் அளவைக் கணக்கிடுவது மட்டுமே; பயிருக்கு ஏற்ற பாசனப் பரிந்துரை அல்ல.",
    },

    "mr": {
        "brand": "RAIDHARA",
        "tagline": "तुमचा बुद्धिमान शेती सहाय्यक",
        "greeting": "नमस्कार, मी तुम्हाला कशी मदत करू शकतो?",
        "listening": "ऐकत आहे...",
        "thinking": "RAIDHARA विचार करत आहे...",
        "speak": "बोलण्यासाठी दाबा",
        "stop": "ऐकणे थांबवा",
        "ask_placeholder": "शेतीबद्दल RAIDHARA ला विचारा...",
        "send": "RAIDHARA ला विचारा",
        "weather": "हवामान",
        "market": "बाजार",
        "crops": "पीक आरोग्य",
        "support": "मदत",
        "weather_title": "हवामान अंदाज",
        "fertilizer_title": "जवळील खतांचे दर",
        "water_title": "पाण्याची गणना",
        "health_title": "पीक आरोग्य तपासणी",
        "soil_title": "माती आणि पीक नियोजन",
        "schemes_title": "सरकारी योजना",
        "city": "शहर",
        "product": "खत",
        "search": "शोधा",
        "area": "शेतीचे क्षेत्रफळ (एकर)",
        "depth": "पाण्याची खोली (मिलीमीटर)",
        "calculate": "पाणी मोजा",
        "crop": "पीक",
        "symptoms": "लक्षणे सांगा",
        "soil_ph": "मातीचा pH, माहीत असल्यास",
        "soil_type": "मातीचा प्रकार",
        "submit": "विश्लेषण करा",
        "schemes_desc": "अधिकृत कृषी योजना पोर्टल पाहा.",
        "demo": "डेमो डेटा — थेट किंवा पडताळलेला नाही",
        "water_result": "अंदाजे पाण्याची गरज",
        "litres": "लिटर",
        "answer": "RAIDHARA चे उत्तर",
        "loading": "तुमच्या प्रश्नावर प्रक्रिया सुरू आहे...",
        "empty": "कृपया प्रश्न लिहा.",
        "error": "काहीतरी चूक झाली.",
        "all": "सर्व",
        "price": "उदाहरणार्थ किंमत",
        "shop": "दुकान",
        "pack": "पॅक",
        "condition": "स्थिती",
        "temperature": "तापमान",
        "not_live": "फक्त उदाहरणे. थेट डेटा जोडलेला नाही.",
        "select_language": "भाषा",
        "health_hint": "पीक, बाधित पाने आणि लक्षणे किती काळापासून आहेत ते सांगा.",
        "soil_hint": "उदाहरण: टोमॅटो, पोयट्याची माती, pH 6.5",
        "water_hint": "क्षेत्रफळ आणि पाण्याची खोली भरा.",
        "no_shops": "या शोधाशी जुळणारी उदाहरणार्थ दुकाने नाहीत.",
        "official": "अधिकृत पोर्टल उघडा",
        "water_note": "ही पाण्याच्या प्रमाणाची गणना आहे; पीक-विशिष्ट सिंचन सल्ला नाही.",
    },
}


def get_language(value):
    """Return a supported language code."""
    if not isinstance(value, str):
        return "en"

    value = value.strip().lower()

    if value in SUPPORTED_LANGUAGES:
        return value

    return "en"


def get_text(value, key):
    language = get_language(value)
    return TRANSLATIONS[language].get(
        key,
        TRANSLATIONS["en"].get(key, key),
    )


# ============================================================
# AI BACKEND
# ============================================================

def make_system_prompt(language, extra_context=""):
    language_name = SUPPORTED_LANGUAGES[get_language(language)]

    return (
        "You are RAIDHARA, a practical agricultural assistant for Indian "
        "farmers. Reply in "
        + language_name
        + " only, except standard scientific units and product names. "
        "Understand complete questions and give useful, actionable answers. "
        "Use short headings or bullet points when helpful. "
        "Never invent current weather, market rates, fertilizer prices, "
        "government rules, or official eligibility. "
        "Do not claim a crop disease is confirmed from symptoms alone. "
        "Do not invent pesticide dosages. Follow product labels and local "
        "agricultural expert guidance. Mention uncertainty where appropriate. "
        + extra_context
    )


def ask_local_ai(question, language="en", extra_context=""):
    """Non-streaming helper for endpoints that need a complete answer."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "stream": False,
            "keep_alive": KEEP_ALIVE,
            "messages": [
                {
                    "role": "system",
                    "content": make_system_prompt(language, extra_context),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            "options": {
                "temperature": 0.2,
                "num_predict": NUM_PREDICT,
                "num_ctx": NUM_CTX,
                "top_k": 20,
                "top_p": 0.8,
            },
        },
        timeout=(10, 180),
    )

    response.raise_for_status()

    answer = response.json().get("message", {}).get("content", "").strip()

    if not answer:
        raise RuntimeError("The model returned an empty answer.")

    return answer


# ============================================================
# MAIN HTML INTERFACE
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>RAIDHARA — AI for Farmers</title>

<style>
:root {
    --bg: #f5f0e6;
    --panel: #20152b;
    --panel-border: #120b19;
    --card: #281d35;
    --card-border: #40314d;
    --purple: #8b5cf6;
    --purple-light: #a78bfa;
    --lime: #c7ff3d;
    --text: #f8f5fb;
    --muted: #a9a0b3;
    --danger: #ff8787;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}

button, input, select, textarea {
    font: inherit;
}

button {
    cursor: pointer;
}

.phone {
    width: min(100%, 390px);
    min-height: 610px;
    height: min(94vh, 850px);
    margin: 2vh auto;
    padding: 24px 18px 18px;
    border: 7px solid var(--panel-border);
    border-radius: 39px;
    background: var(--panel);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
}

.brand {
    color: var(--lime);
    font-size: 18px;
    font-weight: 900;
    letter-spacing: -0.7px;
}

.language {
    width: 112px;
    color: var(--text);
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 9px;
    padding: 7px;
    font-size: 12px;
}

.tagline {
    margin: 5px 0 0;
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.greeting {
    color: #c2b8cb;
    font-size: 15px;
    line-height: 1.55;
    margin: 21px 0 15px;
    min-height: 24px;
}

.voice-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 0 0 10px;
}

.voice-ring {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 2px solid var(--purple);
    background: transparent;
    display: grid;
    place-items: center;
    padding: 0;
    transition: transform .2s, box-shadow .2s;
}

.voice-core {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--purple);
    box-shadow: 0 0 25px #8b5cf655;
}

.voice-ring.listening {
    animation: pulse 1.5s infinite;
    box-shadow: 0 0 25px #8b5cf644;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.06); }
}

.voice-status {
    color: var(--purple-light);
    font-size: 10px;
    letter-spacing: 1px;
    margin-top: 10px;
    min-height: 14px;
    text-align: center;
}

.voice-help {
    color: var(--muted);
    font-size: 11px;
    margin-top: 5px;
    text-align: center;
}

.main-question {
    width: 100%;
    min-height: 70px;
    max-height: 105px;
    resize: vertical;
    border-radius: 12px;
    border: 1px solid var(--card-border);
    background: var(--card);
    color: var(--text);
    padding: 12px;
    margin-top: 12px;
    font-size: 13px;
    outline: none;
}

.main-question:focus,
.field:focus {
    border-color: var(--purple);
}

.primary {
    border: 0;
    border-radius: 10px;
    padding: 12px;
    color: #fff;
    background: var(--purple);
    font-weight: 800;
    font-size: 12px;
    letter-spacing: .4px;
    margin-top: 9px;
}

.primary:disabled {
    opacity: .6;
    cursor: wait;
}

.answer-wrap {
    margin-top: 12px;
    min-height: 0;
    max-height: 155px;
    overflow: auto;
    border-radius: 12px;
    border: 1px solid var(--card-border);
    background: #181020;
    padding: 12px;
}

.answer-title {
    font-size: 10px;
    color: var(--lime);
    font-weight: 800;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.answer {
    font-size: 13px;
    line-height: 1.65;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    color: var(--text);
}

.cards {
    margin-top: auto;
    padding-top: 13px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 11px;
}

.card {
    min-height: 64px;
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 12px;
    color: var(--text);
    text-align: left;
    transition: border-color .2s, transform .2s;
}

.card:hover {
    border-color: var(--purple);
    transform: translateY(-1px);
}

.card-label {
    font-size: 10px;
    font-weight: 800;
    color: #8f8599;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.card-value {
    font-size: 13px;
    font-weight: 650;
    line-height: 1.35;
}

.secondary-nav {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding: 12px 0 3px;
    scrollbar-width: thin;
}

.nav-btn {
    white-space: nowrap;
    border: 1px solid var(--card-border);
    color: #c6bbd0;
    background: var(--card);
    padding: 8px 10px;
    border-radius: 20px;
    font-size: 11px;
}

.nav-btn.active {
    border-color: var(--purple);
    color: var(--lime);
}

.view {
    display: none;
    margin-top: 13px;
    min-height: 0;
    overflow: auto;
    padding-right: 2px;
}

.view.active {
    display: block;
}

.view h2 {
    font-size: 18px;
    margin: 0 0 6px;
}

.description {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.5;
    margin: 0 0 13px;
}

.demo-label {
    color: var(--lime);
    font-size: 9px;
    font-weight: 800;
    letter-spacing: .5px;
    line-height: 1.5;
    margin: 9px 0 12px;
}

.field-label {
    display: block;
    color: #b8aec3;
    font-size: 11px;
    margin: 12px 0 6px;
}

.field {
    width: 100%;
    border: 1px solid var(--card-border);
    background: var(--card);
    color: var(--text);
    padding: 11px;
    border-radius: 9px;
    outline: none;
    font-size: 13px;
}

.field option {
    background: var(--panel);
}

.shop-row, .weather-row, .scheme-row {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 12px;
    margin: 9px 0;
}

.row-title {
    font-size: 12px;
    font-weight: 800;
    line-height: 1.4;
}

.row-sub {
    font-size: 11px;
    color: var(--muted);
    margin-top: 5px;
    line-height: 1.5;
}

.row-price {
    color: var(--lime);
    font-size: 14px;
    font-weight: 800;
    margin-top: 7px;
}

.result-box {
    background: #181020;
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 12px;
    margin-top: 12px;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.scheme-row a {
    display: inline-block;
    margin-top: 8px;
    color: var(--purple-light);
    font-size: 12px;
}

.back-btn {
    border: 0;
    color: var(--purple-light);
    background: transparent;
    padding: 8px 0 12px;
    font-size: 12px;
    text-align: left;
}

.hidden {
    display: none !important;
}

.small-note {
    font-size: 10px;
    color: #a9a0b3;
    line-height: 1.5;
    margin-top: 12px;
}

@media (max-width: 430px) {
    .phone {
        margin: 0 auto;
        width: 100%;
        height: 100dvh;
        min-height: 590px;
        border-radius: 30px;
        border-width: 5px;
    }
}

@media (max-height: 760px) {
    .phone {
        height: 96vh;
        min-height: 570px;
        margin: 2vh auto;
    }

    .voice-ring {
        width: 72px;
        height: 72px;
    }

    .voice-core {
        width: 32px;
        height: 32px;
    }

    .greeting {
        margin: 13px 0 10px;
    }

    .answer-wrap {
        max-height: 110px;
    }
}
</style>
</head>

<body>

<main class="phone">

    <header class="topbar">
        <div>
            <div class="brand" data-i18n="brand">RAIDHARA</div>
            <div class="tagline" data-i18n="tagline">
                Your intelligent farming companion
            </div>
        </div>

        <select id="language" class="language"
                aria-label="Language"
                onchange="changeLanguage(this.value)">
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="te">తెలుగు</option>
            <option value="kn">ಕನ್ನಡ</option>
            <option value="ta">தமிழ்</option>
            <option value="mr">मराठी</option>
        </select>
    </header>

    <!-- MAIN VOICE-FIRST SCREEN -->
    <section id="home">

        <p class="greeting" data-i18n="greeting">
            Hello, how can I help you?
        </p>

        <div class="voice-area">
            <button id="voiceButton" class="voice-ring"
                    onclick="toggleListening()"
                    aria-label="Speak to RAIDHARA">
                <span class="voice-core"></span>
            </button>

            <div id="voiceStatus" class="voice-status"
                 data-i18n="speak">TAP TO SPEAK</div>

            <div class="voice-help" id="voiceHelp"></div>
        </div>

        <textarea id="question" class="main-question"
                  data-i18n-placeholder="ask_placeholder"
                  placeholder="Ask RAIDHARA anything about farming..."
                  maxlength="2000"></textarea>

        <button id="askButton" class="primary"
                onclick="askAI()" data-i18n="send">
            ASK RAIDHARA
        </button>

        <div id="answerWrap" class="answer-wrap hidden">
            <div class="answer-title" data-i18n="answer">
                RAIDHARA RESPONSE
            </div>
            <div id="answer" class="answer" aria-live="polite"></div>
        </div>

    </section>

    <!-- ORIGINAL-STYLE SHORTCUT CARDS -->
    <section class="cards" id="homeCards">

        <button class="card" onclick="openView('weatherView')">
            <div class="card-label" data-i18n="weather">WEATHER</div>
            <div class="card-value" id="weatherSummary">25°C • Demo</div>
        </button>

        <button class="card" onclick="openView('fertilizerView')">
            <div class="card-label" data-i18n="market">MARKET</div>
            <div class="card-value" id="marketSummary">Fertilizer prices</div>
        </button>

        <button class="card" onclick="openView('healthView')">
            <div class="card-label" data-i18n="crops">CROP HEALTH</div>
            <div class="card-value" data-i18n="health_title">
                Crop Health Check
            </div>
        </button>

        <button class="card" onclick="openView('schemesView')">
            <div class="card-label" data-i18n="support">SUPPORT</div>
            <div class="card-value" data-i18n="schemes_title">
                Government Schemes
            </div>
        </button>

    </section>

    <!-- SECONDARY SECTIONS -->
    <nav id="sectionNav" class="secondary-nav hidden">
        <button class="nav-btn" onclick="openView('weatherView')"
                data-i18n="weather">Weather</button>
        <button class="nav-btn" onclick="openView('fertilizerView')"
                data-i18n="market">Market</button>
        <button class="nav-btn" onclick="openView('waterView')"
                data-i18n="water_title">Water</button>
        <button class="nav-btn" onclick="openView('healthView')"
                data-i18n="crops">Crop health</button>
        <button class="nav-btn" onclick="openView('soilView')"
                data-i18n="soil_title">Soil</button>
        <button class="nav-btn" onclick="openView('schemesView')"
                data-i18n="support">Support</button>
    </nav>

    <!-- WEATHER -->
    <section id="weatherView" class="view">
        <button class="back-btn" onclick="goHome()">← RAIDHARA</button>

        <h2 data-i18n="weather_title">Weather Forecast</h2>
        <p class="description" data-i18n="not_live">
            Demonstration values only. Live data is not connected.
        </p>

        <div class="demo-label" data-i18n="demo">
            DEMO DATA — NOT LIVE OR VERIFIED
        </div>

        <label class="field-label" data-i18n="city">City</label>
        <select id="weatherCity" class="field">
            <option value="Bengaluru">Bengaluru</option>
            <option value="Mangaluru">Mangaluru</option>
            <option value="Mysuru">Mysuru</option>
            <option value="Hubballi">Hubballi</option>
        </select>

        <button class="primary" onclick="loadWeather()"
                data-i18n="search">SEARCH</button>

        <div id="weatherResults"></div>
    </section>

    <!-- FERTILIZER SHOPS -->
    <section id="fertilizerView" class="view">
        <button class="back-btn" onclick="goHome()">← RAIDHARA</button>

        <h2 data-i18n="fertilizer_title">Nearby Fertilizer Prices</h2>

        <p class="description" data-i18n="not_live">
            Demonstration values only. Live data is not connected.
        </p>

        <div class="demo-label" data-i18n="demo">
            DEMO DATA — NOT LIVE OR VERIFIED
        </div>

        <label class="field-label" data-i18n="city">City</label>
        <select id="fertilizerCity" class="field">
            <option value="All">All</option>
            <option value="Bengaluru">Bengaluru</option>
            <option value="Mangaluru">Mangaluru</option>
            <option value="Mysuru">Mysuru</option>
        </select>

        <label class="field-label" data-i18n="product">Fertilizer</label>
        <select id="fertilizerProduct" class="field">
            <option value="All">All</option>
            <option value="Urea">Urea</option>
            <option value="NPK 19:19:19">NPK 19:19:19</option>
            <option value="Neem cake">Neem cake</option>
            <option value="Vermicompost">Vermicompost</option>
        </select>

        <button class="primary" onclick="loadFertilizers()"
                data-i18n="search">SEARCH</button>

        <div id="fertilizerResults"></div>
    </section>

    <!-- WATER CALCULATOR -->
    <section id="waterView" class="view">
        <button class="back-btn" onclick="goHome()">← RAIDHARA</button>

        <h2 data-i18n="water_title">Water Calculator</h2>

        <p class="description" data-i18n="water_hint">
            Enter the area and irrigation depth.
        </p>

        <label class="field-label" data-i18n="area">
            Farm area in acres
        </label>
        <input id="waterArea" class="field" type="number"
               min="0.01" max="100000" step="any" value="1">

        <label class="field-label" data-i18n="depth">
            Water depth in millimetres
        </label>
        <input id="waterDepth" class="field" type="number"
               min="0.1" max="1000" step="any" value="10">

        <button class="primary" onclick="calculateWater()"
                data-i18n="calculate">CALCULATE WATER</button>

        <div id="waterResults" class="result-box hidden"></div>

        <p class="small-note" data-i18n="water_note">
            This is a volume calculation, not a crop-specific irrigation
            recommendation.
        </p>
    </section>

    <!-- CROP HEALTH -->
    <section id="healthView" class="view">
        <button class="back-btn" onclick="goHome()">← RAIDHARA</button>

        <h2 data-i18n="health_title">Crop Health Check</h2>

        <p class="description" data-i18n="health_hint">
            Describe the crop, affected leaves, and how long symptoms
            have been present.
        </p>

        <label class="field-label" data-i18n="crop">Crop</label>
        <input id="healthCrop" class="field"
               placeholder="Tomato, rice, chilli...">

        <label class="field-label" data-i18n="symptoms">Symptoms</label>
        <textarea id="healthSymptoms" class="field"
                  rows="4"
                  data-i18n-placeholder="health_hint"
                  placeholder="Describe the symptoms..."></textarea>

        <button class="primary" onclick="checkCropHealth()"
                data-i18n="submit">ANALYSE</button>

        <div id="healthResults" class="result-box hidden"></div>
    </section>

    <!-- SOIL AND CROP PLANNING -->
    <section id="soilView" class="view">
        <button class="back-btn" onclick="goHome()">← RAIDHARA</button>

        <h2 data-i18n="soil_title">Soil & Crop Planning</h2>

        <label class="field-label" data-i18n="crop">Crop</label>
        <input id="soilCrop" class="field"
               placeholder="Tomato, rice, maize...">

        <label class="field-label" data-i18n="soil_type">Soil type</label>
        <select id="soilType" class="field">
            <option value="Unknown">Unknown</option>
            <option value="Sandy">Sandy</option>
            <option value="Clay">Clay</option>
            <option value="Loamy">Loamy</option>
            <option value="Black soil">Black soil</option>
            <option value="Red soil">Red soil</option>
        </select>

        <label class="field-label" data-i18n="soil_ph">
            Soil pH, if known
        </label>
        <input id="soilPH" class="field" type="number"
               min="0" max="14" step="0.1" placeholder="6.5">

        <label class="field-label" data-i18n="city">City</label>
        <input id="soilCity" class="field" placeholder="Bengaluru">

        <button class="primary" onclick="planSoil()"
                data-i18n="submit">ANALYSE</button>

        <div id="soilResults" class="result-box hidden"></div>
    </section>

    <!-- GOVERNMENT SCHEMES -->
    <section id="schemesView" class="view">
        <button class="back-btn" onclick="goHome()">← RAIDHARA</button>

        <h2 data-i18n="schemes_title">Government Schemes</h2>

        <p class="description" data-i18n="schemes_desc">
            Explore official agricultural scheme portals.
        </p>

        <div class="scheme-row">
            <div class="row-title">MyScheme</div>
            <div class="row-sub">
                Government scheme discovery and eligibility information.
            </div>
            <a href="https://www.myscheme.gov.in/"
               target="_blank" rel="noopener noreferrer"
               data-i18n="official">Open official portal</a>
        </div>

        <div class="scheme-row">
            <div class="row-title">PM Fasal Bima Yojana</div>
            <div class="row-sub">
                Crop insurance information.
            </div>
            <a href="https://pmfby.gov.in/"
               target="_blank" rel="noopener noreferrer"
               data-i18n="official">Open official portal</a>
        </div>

        <div class="scheme-row">
            <div class="row-title">e-NAM</div>
            <div class="row-sub">
                National Agriculture Market information.
            </div>
            <a href="https://enam.gov.in/"
               target="_blank" rel="noopener noreferrer"
               data-i18n="official">Open official portal</a>
        </div>

        <div class="scheme-row">
            <div class="row-title">Agmarknet</div>
            <div class="row-sub">
                Agricultural marketing and mandi information.
            </div>
            <a href="https://agmarknet.gov.in/"
               target="_blank" rel="noopener noreferrer"
               data-i18n="official">Open official portal</a>
        </div>

        <p class="small-note">
            Verify current eligibility, deadlines and benefits on the
            relevant official portal. RAIDHARA does not automatically
            confirm scheme eligibility.
        </p>
    </section>

</main>

<script>
const I18N = {{ translations | tojson }};
const LANGUAGES = {
    en: "en-IN",
    hi: "hi-IN",
    te: "te-IN",
    kn: "kn-IN",
    ta: "ta-IN",
    mr: "mr-IN"
};

let language = localStorage.getItem("raidhara_language") || "en";
let recognition = null;
let listening = false;
let stopTimer = null;
let finalTranscript = "";
let activeView = "home";
let lastAnswer = "";
let speechGeneration = 0;

function T(key) {
    return (I18N[language] && I18N[language][key]) ||
           I18N.en[key] || key;
}

function changeLanguage(newLanguage) {
    language = I18N[newLanguage] ? newLanguage : "en";

    localStorage.setItem("raidhara_language", language);

    document.documentElement.lang = language;
    document.getElementById("language").value = language;

    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.dataset.i18n;
        element.textContent = T(key);
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
        element.placeholder = T(element.dataset.i18nPlaceholder);
    });

    // Change the speech recognition and speech synthesis languages too.
    if (recognition && listening) {
        stopListening(false);
    }

    document.getElementById("voiceStatus").textContent = T("speak");

    // Refresh translated dynamic sections.
    if (activeView === "weatherView") loadWeather();
    if (activeView === "fertilizerView") loadFertilizers();

    // Existing generated answers cannot be reliably translated by changing
    // a dropdown. If desired, ask the AI to translate them explicitly.
}

function openView(viewId) {
    activeView = viewId;

    document.getElementById("home").classList.add("hidden");
    document.getElementById("homeCards").classList.add("hidden");
    document.getElementById("sectionNav").classList.remove("hidden");

    document.querySelectorAll(".view").forEach(view => {
        view.classList.toggle("active", view.id === viewId);
    });

    document.querySelectorAll(".nav-btn").forEach(button => {
        button.classList.toggle(
            "active",
            button.getAttribute("onclick").includes(viewId)
        );
    });

    if (viewId === "weatherView") loadWeather();
    if (viewId === "fertilizerView") loadFertilizers();
}

function goHome() {
    activeView = "home";

    document.getElementById("home").classList.remove("hidden");
    document.getElementById("homeCards").classList.remove("hidden");
    document.getElementById("sectionNav").classList.add("hidden");

    document.querySelectorAll(".view").forEach(view => {
        view.classList.remove("active");
    });
}

function setVoiceStatus(message) {
    document.getElementById("voiceStatus").textContent = message;
}

function stopListening(updateStatus = true) {
    clearTimeout(stopTimer);

    if (recognition) {
        try {
            recognition.onresult = null;
            recognition.onend = null;
            recognition.onerror = null;
            recognition.stop();
        } catch (e) {}
    }

    recognition = null;
    listening = false;

    document.getElementById("voiceButton").classList.remove("listening");

    if (updateStatus) setVoiceStatus(T("speak"));
}

function toggleListening() {
    if (listening) {
        stopListening(true);
        return;
    }

    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        setVoiceStatus("Voice unavailable — use Chrome or type your question.");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = LANGUAGES[language] || "en-IN";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    listening = true;
    finalTranscript = "";

    document.getElementById("voiceButton").classList.add("listening");
    setVoiceStatus(T("listening"));

    const input = document.getElementById("question");
    input.value = "";

    recognition.onresult = event => {
        let interim = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];

            if (result.isFinal) {
                finalTranscript += result[0].transcript + " ";
            } else {
                interim += result[0].transcript;
            }
        }

        input.value = (finalTranscript + interim).trim();

        clearTimeout(stopTimer);

        // Submit after a natural pause, rather than after each short phrase.
        stopTimer = setTimeout(() => {
            stopListening(false);

            if (input.value.trim()) {
                askAI();
            } else {
                setVoiceStatus(T("speak"));
            }
        }, 2200);
    };

    recognition.onerror = event => {
        stopListening(false);
        setVoiceStatus("Voice error: " + event.error);
    };

    recognition.onend = () => {
        if (!listening) return;

        // Some browsers stop recognition automatically.
        stopListening(false);

        if (input.value.trim()) {
            askAI();
        } else {
            setVoiceStatus(T("speak"));
        }
    };

    try {
        recognition.start();
    } catch (error) {
        stopListening(false);
        setVoiceStatus("Could not start microphone.");
    }

    // Safety limit.
    stopTimer = setTimeout(() => {
        if (listening) {
            stopListening(false);

            if (input.value.trim()) askAI();
        }
    }, 30000);
}

async function streamAI(question, outputElement) {
    const response = await fetch("/api/ask-stream", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            question: question,
            language: language
        })
    });

    if (!response.ok) {
        let errorMessage = "AI request failed.";

        try {
            const data = await response.json();
            errorMessage = data.error || errorMessage;
        } catch (e) {}

        throw new Error(errorMessage);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let completeAnswer = "";

    while (true) {
        const {value, done} = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, {stream: true});

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
            if (!line.trim()) continue;

            const item = JSON.parse(line);

            if (item.error) throw new Error(item.error);

            if (item.token) {
                completeAnswer += item.token;
                outputElement.textContent = completeAnswer;
                outputElement.scrollTop = outputElement.scrollHeight;
            }
        }
    }

    if (buffer.trim()) {
        const item = JSON.parse(buffer);

        if (item.error) throw new Error(item.error);

        if (item.token) completeAnswer += item.token;
    }

    outputElement.textContent = completeAnswer;

    return completeAnswer;
}

async function askAI() {
    const input = document.getElementById("question");
    const question = input.value.trim();

    if (!question) {
        setVoiceStatus(T("empty"));
        return;
    }

    const button = document.getElementById("askButton");
    const wrap = document.getElementById("answerWrap");
    const output = document.getElementById("answer");

    button.disabled = true;
    wrap.classList.remove("hidden");
    output.textContent = T("loading");

    setVoiceStatus(T("thinking"));

    try {
        lastAnswer = await streamAI(question, output);

        if (!lastAnswer.trim()) {
            throw new Error("Empty AI response.");
        }

        setVoiceStatus("ANSWER READY");

    } catch (error) {
        output.textContent = T("error") + " " + error.message;
        setVoiceStatus("REQUEST FAILED");

    } finally {
        button.disabled = false;
    }
}

async function postJSON(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            ...payload,
            language: language
        })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }

    return data;
}

function showResult(id, text) {
    const element = document.getElementById(id);
    element.classList.remove("hidden");
    element.textContent = text;
}

async function loadWeather() {
    const city = document.getElementById("weatherCity").value;
    const container = document.getElementById("weatherResults");

    container.textContent = T("loading");

    try {
        const response = await fetch(
            "/api/weather?city=" + encodeURIComponent(city) +
            "&language=" + encodeURIComponent(language)
        );

        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Weather unavailable.");

        container.innerHTML = "";

        const label = document.createElement("div");
        label.className = "demo-label";
        label.textContent = T("demo");
        container.appendChild(label);

        data.items.forEach(item => {
            const row = document.createElement("div");
            row.className = "weather-row";

            const title = document.createElement("div");
            title.className = "row-title";
            title.textContent = item.city + " — " + item.temperature + "°C";

            const sub = document.createElement("div");
            sub.className = "row-sub";
            sub.textContent = item.condition;

            row.appendChild(title);
            row.appendChild(sub);
            container.appendChild(row);
        });

        if (data.items.length === 0) {
            container.textContent = T("not_live");
        }

    } catch (error) {
        container.textContent = T("error") + " " + error.message;
    }
}

async function loadFertilizers() {
    const city = document.getElementById("fertilizerCity").value;
    const product = document.getElementById("fertilizerProduct").value;
    const container = document.getElementById("fertilizerResults");

    container.textContent = T("loading");

    try {
        const params = new URLSearchParams({
            city: city,
            product: product,
            language: language
        });

        const response = await fetch("/api/fertilizers?" + params.toString());
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Prices unavailable.");

        container.innerHTML = "";

        const label = document.createElement("div");
        label.className = "demo-label";
        label.textContent = T("demo");
        container.appendChild(label);

        data.items.forEach(item => {
            const row = document.createElement("div");
            row.className = "shop-row";

            const title = document.createElement("div");
            title.className = "row-title";
            title.textContent = item.shop;

            const sub = document.createElement("div");
            sub.className = "row-sub";
            sub.textContent = item.city + " • " + item.product +
                " • " + item.pack;

            const price = document.createElement("div");
            price.className = "row-price";
            price.textContent = "₹" + Number(item.price).toFixed(2);

            row.appendChild(title);
            row.appendChild(sub);
            row.appendChild(price);

            container.appendChild(row);
        });

        if (data.items.length === 0) {
            container.textContent = T("no_shops");
        }

    } catch (error) {
        container.textContent = T("error") + " " + error.message;
    }
}

async function calculateWater() {
    const area = Number(document.getElementById("waterArea").value);
    const depth = Number(document.getElementById("waterDepth").value);

    try {
        const data = await postJSON("/api/water", {
            area_acres: area,
            depth_mm: depth
        });

        showResult(
            "waterResults",
            T("water_result") + ": " +
            data.litres.toLocaleString() + " " + T("litres") +
            "\n\n" + T("water_note")
        );

    } catch (error) {
        showResult("waterResults", T("error") + " " + error.message);
    }
}

async function checkCropHealth() {
    const crop = document.getElementById("healthCrop").value.trim();
    const symptoms = document.getElementById("healthSymptoms").value.trim();

    if (!crop || !symptoms) {
        showResult("healthResults", T("empty"));
        return;
    }

    showResult("healthResults", T("loading"));

    try {
        const data = await postJSON("/api/crop-health", {
            crop: crop,
            symptoms: symptoms
        });

        showResult("healthResults", data.answer);

    } catch (error) {
        showResult("healthResults", T("error") + " " + error.message);
    }
}

async function planSoil() {
    const crop = document.getElementById("soilCrop").value.trim();
    const soilType = document.getElementById("soilType").value;
    const ph = document.getElementById("soilPH").value;
    const city = document.getElementById("soilCity").value.trim();

    if (!crop) {
        showResult("soilResults", T("empty"));
        return;
    }

    showResult("soilResults", T("loading"));

    try {
        const data = await postJSON("/api/soil-plan", {
            crop: crop,
            soil_type: soilType,
            ph: ph,
            city: city
        });

        showResult("soilResults", data.answer);

    } catch (error) {
        showResult("soilResults", T("error") + " " + error.message);
    }
}

// Restore the last selected language.
changeLanguage(language);

// Load demonstration values for the initial screen.
fetch("/api/weather?city=Bengaluru&language=en")
    .then(response => response.json())
    .then(data => {
        if (data.items && data.items.length) {
            document.getElementById("weatherSummary").textContent =
                data.items[0].temperature + "°C • Demo";
        }
    })
    .catch(() => {});
</script>

</body>
</html>
"""


# ============================================================
# PAGE ROUTE
# ============================================================

@app.route("/")
def home():
    return render_template_string(
        HTML,
        translations=TRANSLATIONS,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    try:
        response = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=3,
        )
        response.raise_for_status()

        models = [
            item.get("name", "")
            for item in response.json().get("models", [])
        ]

        return jsonify({
            "status": "ok",
            "ollama": "connected",
            "configured_model": MODEL,
            "configured_model_available": any(
                name == MODEL or name.startswith(MODEL + ":")
                for name in models
            ),
            "available_models": models,
        })

    except requests.RequestException:
        return jsonify({
            "status": "degraded",
            "ollama": "unavailable",
            "message": "Start Ollama and check that it is listening on port 11434.",
        }), 503


# ============================================================
# STREAMING AI ENDPOINT
# ============================================================

@app.route("/api/ask-stream", methods=["POST"])
def api_ask_stream():
    data = request.get_json(silent=True) or {}

    question = str(data.get("question", "")).strip()
    language = get_language(data.get("language"))

    if not question:
        return jsonify({
            "error": get_text(language, "empty"),
        }), 400

    if len(question) > 2000:
        return jsonify({
            "error": "Question is too long. Please use fewer than 2000 characters.",
        }), 400

    def generate():
        start_time = time.time()

        try:
            with requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "stream": True,
                    "keep_alive": KEEP_ALIVE,
                    "messages": [
                        {
                            "role": "system",
                            "content": make_system_prompt(language),
                        },
                        {
                            "role": "user",
                            "content": question,
                        },
                    ],
                    "options": {
                        "temperature": 0.2,
                        "num_predict": NUM_PREDICT,
                        "num_ctx": NUM_CTX,
                        "top_k": 20,
                        "top_p": 0.8,
                    },
                },
                stream=True,
                timeout=(10, 180),
            ) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    item = json.loads(line.decode("utf-8"))

                    content = item.get("message", {}).get("content", "")

                    if content:
                        yield json.dumps({
                            "token": content,
                        }, ensure_ascii=False) + "\n"

                    if item.get("done"):
                        yield json.dumps({
                            "done": True,
                            "elapsed_seconds": round(
                                time.time() - start_time, 2
                            ),
                        }) + "\n"

        except Exception as error:
            yield json.dumps({
                "error": (
                    "RAIDHARA could not reach the AI model. "
                    "Check that Ollama is running and that "
                    + MODEL
                    + " is installed. Details: "
                    + str(error)
                ),
            }, ensure_ascii=False) + "\n"

    return Response(
        stream_with_context(generate()),
        content_type="application/x-ndjson; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# WEATHER ENDPOINT
# ============================================================

@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    language = get_language(request.args.get("language"))

    items = [
        item for item in WEATHER_DEMO
        if not city or item["city"].lower() == city.lower()
    ]

    return jsonify({
        "source": "DEMO — NOT LIVE WEATHER",
        "is_live": False,
        "notice": get_text(language, "not_live"),
        "items": items,
    })


# ============================================================
# FERTILIZER PRICE ENDPOINT
# ============================================================

@app.route("/api/fertilizers")
def api_fertilizers():
    city = request.args.get("city", "All").strip()
    product = request.args.get("product", "All").strip()
    language = get_language(request.args.get("language"))

    items = FERTILIZER_SHOPS_DEMO

    if city and city.lower() != "all":
        items = [
            item for item in items
            if item["city"].lower() == city.lower()
        ]

    if product and product.lower() != "all":
        items = [
            item for item in items
            if item["product"].lower() == product.lower()
        ]

    return jsonify({
        "source": "DEMO — NOT LIVE OR VERIFIED SHOP PRICES",
        "is_live": False,
        "notice": get_text(language, "not_live"),
        "items": items,
    })


# ============================================================
# WATER CALCULATOR
# ============================================================

@app.route("/api/water", methods=["POST"])
def api_water():
    data = request.get_json(silent=True) or {}

    try:
        area = float(data.get("area_acres", 0))
        depth = float(data.get("depth_mm", 0))
    except (TypeError, ValueError):
        return jsonify({
            "error": "Enter valid numeric values.",
        }), 400

    if not (0 < area <= 100000):
        return jsonify({
            "error": "Farm area must be greater than 0 and at most 100000 acres.",
        }), 400

    if not (0 < depth <= 1000):
        return jsonify({
            "error": "Water depth must be greater than 0 and at most 1000 mm.",
        }), 400

    # 1 acre = approximately 4046.8564224 square metres.
    # 1 mm of water over 1 square metre = 1 litre.
    litres = area * 4046.8564224 * depth

    return jsonify({
        "area_acres": area,
        "depth_mm": depth,
        "litres": round(litres, 2),
        "cubic_metres": round(litres / 1000, 2),
        "note": (
            "Theoretical water volume. Actual crop requirements depend "
            "on soil, crop stage, rainfall, irrigation efficiency, "
            "and local conditions."
        ),
    })


# ============================================================
# CROP HEALTH ENDPOINT
# ============================================================

@app.route("/api/crop-health", methods=["POST"])
def api_crop_health():
    data = request.get_json(silent=True) or {}

    crop = str(data.get("crop", "")).strip()
    symptoms = str(data.get("symptoms", "")).strip()
    language = get_language(data.get("language"))

    if not crop or not symptoms:
        return jsonify({
            "error": get_text(language, "empty"),
        }), 400

    if len(crop) > 150 or len(symptoms) > 2000:
        return jsonify({
            "error": "Please shorten the input and try again.",
        }), 400

    question = (
        "Help assess these crop symptoms.\n"
        "Crop: " + crop + "\n"
        "Observed symptoms: " + symptoms + "\n\n"
        "Explain two or three plausible causes, what observations could "
        "help distinguish them, and safe immediate steps. Ask for missing "
        "details if needed. Do not claim a confirmed diagnosis. Do not "
        "prescribe unsupported pesticide doses. Recommend local agricultural "
        "expert help if the problem is spreading or severe."
    )

    try:
        answer = ask_local_ai(
            question,
            language=language,
            extra_context=(
                "This is a crop-health triage task. Do not claim certainty "
                "without sufficient evidence."
            ),
        )

        return jsonify({
            "answer": answer,
            "is_confirmed_diagnosis": False,
        })

    except requests.RequestException as error:
        return jsonify({
            "error": "The local AI service is unavailable: " + str(error),
        }), 503

    except Exception as error:
        app.logger.exception("Crop health request failed")

        return jsonify({
            "error": "Crop health request failed: " + str(error),
        }), 500


# ============================================================
# SOIL AND CROP PLANNING ENDPOINT
# ============================================================

@app.route("/api/soil-plan", methods=["POST"])
def api_soil_plan():
    data = request.get_json(silent=True) or {}

    crop = str(data.get("crop", "")).strip()
    soil_type = str(data.get("soil_type", "Unknown")).strip()
    ph_value = str(data.get("ph", "")).strip()
    city = str(data.get("city", "")).strip()
    language = get_language(data.get("language"))

    if not crop:
        return jsonify({
            "error": get_text(language, "empty"),
        }), 400

    if len(crop) > 150 or len(soil_type) > 100 or len(city) > 150:
        return jsonify({
            "error": "Please shorten the input and try again.",
        }), 400

    if ph_value:
        try:
            ph_number = float(ph_value)
            if not 0 <= ph_number <= 14:
                raise ValueError()
        except ValueError:
            return jsonify({
                "error": "Soil pH must be a number between 0 and 14.",
            }), 400

    question = (
        "Provide a preliminary soil and crop planning guide.\n"
        "Crop: " + crop + "\n"
        "Soil type: " + (soil_type or "Unknown") + "\n"
        "Soil pH: " + (ph_value or "Not provided") + "\n"
        "Location: " + (city or "Not provided") + "\n\n"
        "Explain what additional soil-test results would be useful, "
        "general crop planning considerations, and appropriate next steps. "
        "Do not invent soil-test values, current weather, local regulations, "
        "or exact fertilizer doses. Encourage a laboratory soil test and "
        "local agricultural advice where appropriate."
    )

    try:
        answer = ask_local_ai(
            question,
            language=language,
            extra_context=(
                "This is preliminary guidance, not a substitute for "
                "laboratory soil testing or local agricultural advice."
            ),
        )

        return jsonify({
            "answer": answer,
        })

    except requests.RequestException as error:
        return jsonify({
            "error": "The local AI service is unavailable: " + str(error),
        }), 503

    except Exception as error:
        app.logger.exception("Soil planning request failed")

        return jsonify({
            "error": "Soil planning failed: " + str(error),
        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("RAIDHARA — AI FARMING ASSISTANT")
    print("=" * 50)
    print("Model:", MODEL)
    print("Ollama:", OLLAMA_URL)
    print("Open: http://127.0.0.1:5000")
    print("Health check: http://127.0.0.1:5000/health")
    print("Demo weather: http://127.0.0.1:5000/api/weather")
    print("Demo fertilizer prices: http://127.0.0.1:5000/api/fertilizers")
    print("=" * 50)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
    )