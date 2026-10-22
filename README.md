RAIDHARA — AI Voice Assistant for Farmers

RAIDHARA is a prototype of a voice-first AI agricultural assistant designed to make farming information more accessible to Indian farmers through natural-language interaction and regional language support.

Built by Mithrava Technologies.

🚀 Prototype Features
🎙️ AI Voice Assistant — Interact with RAIDHARA using voice or text.
🌐 Regional Languages — Designed to support multiple Indian languages.
🌦️ Weather Information — View example weather information for selected locations.
🌱 Fertilizer Information — Explore fertilizer products, example prices, and nearby shop listings.
🧪 Crop Health Guidance — Get preliminary guidance based on crop symptoms.
💧 Water Planning — Estimate irrigation water requirements using user-provided inputs.
🌾 Agricultural Market Information — Explore agricultural market-related information.
🏛️ Government Schemes — Access information about agricultural support and farmer welfare schemes.
🛠️ Technology Stack
Python
Flask
Ollama with a locally hosted language model
HTML, CSS, and JavaScript
Browser-based speech recognition and text-to-speech, where supported
💻 Running the Prototype Locally
Prerequisites
Python 3.10 or a compatible version
Ollama
The language model configured in the application
A modern web browser
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/RAIDHARA.git
cd RAIDHARA
2. Create a virtual environment
python -m venv venv

Activate it on Windows PowerShell:

.\venv\Scripts\Activate.ps1
3. Install dependencies
pip install -r requirements.txt
4. Set up the AI model

If the application is configured to use qwen2.5:3b, run:

ollama pull qwen2.5:3b

Ensure that Ollama is running before starting the application.

5. Launch RAIDHARA
python app.py

Open the local address displayed in the terminal, typically:

http://127.0.0.1:5000

⚠️ Prototype Limitations

RAIDHARA is currently a prototype and is under active development.

Example fertilizer shops and prices are illustrative and should not be treated as verified local market prices.
Weather values are demonstrations unless a live weather API is connected.
AI-generated agricultural guidance may be inaccurate and should be verified before making important farming decisions.
Voice features depend on browser capabilities and permissions.
Availability of live market prices, government scheme information, and other external data depends on the integrations configured in the application.
🔮 Future Scope
Integration with verified agricultural data sources.
Live local fertilizer prices and shop information.
Real-time weather forecasts and agricultural alerts.
Improved multilingual voice interactions.
More reliable crop health assistance.
Offline and low-connectivity support.
Integration with agricultural experts and official resources.
