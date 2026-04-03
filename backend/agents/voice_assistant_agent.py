"""
🎤 VOICE ASSISTANT AGENT
Multilingual voice assistant (Hindi/Marathi/English)
"""
from typing import Dict, Any
from datetime import datetime
import re

class VoiceAssistantAgent:
    def __init__(self, database):
        self.db = database
        self.name = "Voice Assistant"
        
        # Multilingual commands
        self.commands = {
            "en": {
                "weather": ["weather", "forecast", "rain", "temperature"],
                "water": ["irrigation", "water", "irrigate", "watering"],
                "soil": ["soil", "moisture", "ph", "nutrients"],
                "disease": ["disease", "sick", "problem", "pest"],
                "market": ["price", "market", "sell", "mandi"],
                "schemes": ["scheme", "subsidy", "government", "loan"],
                "help": ["help", "assist", "how", "what"]
            },
            "hi": {  # Hindi (Both Devanagari and Romanized)
                "weather": ["mausam", "barish", "tapman", "मौसम", "बारिश", "तापमान", "weather"],
                "water": ["pani", "sinchai", "paani", "पानी", "सिंचाई", "irrigation"],
                "soil": ["mitti", "bhoomi", "मिट्टी", "भूमि", "soil"],
                "disease": ["bimari", "rog", "keeda", "बीमारी", "रोग", "कीड़ा", "disease"],
                "market": ["daam", "bazaar", "mandi", "kimmat", "दाम", "बाजार", "मंडी", "किम्मत", "market", "price"],
                "schemes": ["yojana", "sahayata", "loan", "योजना", "साहायता", "scheme"],
                "help": ["madad", "sahayata", "kaise", "मदद", "साहायता", "कैसे", "help"]
            },
            "mr": {  # Marathi (Both Devanagari and Romanized)
                "weather": ["hawa", "paus", "tapa", "हवा", "पाऊस", "तापमान", "मौसम", "weather"],
                "water": ["pani", "panyacha", "पाणी", "पाण्याचा", "सिंचन", "sinchan", "irrigation"],
                "soil": ["maati", "jamin", "माती", "जमीन", "मृदा", "soil"],
                "disease": ["rog", "ajar", "रोग", "आजार", "बीमारी", "disease"],
                "market": ["kimmat", "bazaar", "bhav", "gavha", "किंमत", "बाजार", "मंडी", "भाव", "गव्हा", "गव्हाची", "दर", "market", "price"],
                "schemes": ["yojna", "sahaya", "योजना", "साहाय्य", "सरकारी", "scheme"],
                "help": ["madad", "kashi", "मदत", "कशी", "help", "काय"]
            }
        }
        
        # Responses in multiple languages
        self.responses = {
            "en": {
                "greeting": "Hello! I'm your Smart Farming Assistant. How can I help you today?",
                "weather": "Let me check the weather forecast for you.",
                "water": "I'll analyze your irrigation needs.",
                "soil": "I'll check your soil health status.",
                "disease": "I'll scan for crop diseases.",
                "market": "I'll get the latest market prices.",
                "schemes": "I'll find applicable government schemes for you.",
                "unknown": "I didn't understand that. Please try: weather, irrigation, soil, disease, market, or schemes."
            },
            "hi": {
                "greeting": "Namaste! Main aapka Smart Farming Assistant hoon. Main aapki kaise madad kar sakta hoon?",
                "weather": "Main aapke liye mausam ki jankari dekh raha hoon.",
                "water": "Main aapki sinchai ki zaroorat ka vishleshan kar raha hoon.",
                "soil": "Main aapki mitti ki sehat jaanch raha hoon.",
                "disease": "Main fasal ki bimaariyon ki jaanch kar raha hoon.",
                "market": "Main taaza baazaar ke daam dekh raha hoon.",
                "schemes": "Main aapke liye sarkari yojanaaon ki jankari de raha hoon.",
                "unknown": "Main samajh nahi paya. Kripya poochhiye: mausam, sinchai, mitti, bimari, bazaar, ya yojana."
            },
            "mr": {
                "greeting": "नमस्कार! मी तुमचा Smart Farming Assistant आहे. मी तुमची कशी मदत करू शकतो?",
                "weather": "मी तुमच्यासाठी हवामानाची माहिती पाहतो आहे.",
                "water": "मी तुमच्या सिंचनाची गरज तपासतो आहे.",
                "soil": "मी तुमची मातीची आरोग्य स्थिती तपासतो आहे.",
                "disease": "मी पिकांच्या रोगांची तपासणी करतो आहे.",
                "market": "मी ताजा बाजार किंमत पाहतो आहे.",
                "schemes": "मी तुमच्यासाठी सरकारी योजना शोधत आहे.",
                "unknown": "मला समजले नाही. कृपया विचारा: हवामान, पाणी, माती, रोग, बाजार, योजना."
            }
        }
    
    def process_command(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Process voice/text command and return response"""
        
        # Auto-detect language if not specified or if text contains non-English chars
        detected_lang = self._detect_language(text)
        if detected_lang and detected_lang != language:
            print(f"🔍 Auto-detected language: {detected_lang} (overriding {language})")
            language = detected_lang
        
        result = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "input_text": text,
            "language": language,
            "detected_language": detected_lang,
            "intent": "unknown",
            "response_text": "",
            "action_taken": "",
            "data": {},
            "blockchain_logged": False,
            "green_tokens_earned": 0
        }
        
        # Normalize text
        text_lower = text.lower()
        
        # Check for eco-friendly actions FIRST (to log to blockchain)
        eco_action = self._detect_eco_action(text_lower, language)
        if eco_action:
            result["intent"] = "eco_action"
            result["eco_action_type"] = eco_action["action_type"]
            result["green_tokens_earned"] = eco_action["tokens"]
            
            # Log to blockchain
            blockchain_result = self._log_to_blockchain(eco_action, language)
            result["blockchain_logged"] = blockchain_result.get("success", False)
            result["data"] = blockchain_result
            
            responses = self.responses.get(language, self.responses["en"])
            if language == "en":
                result["response_text"] = f"Excellent! You've earned {eco_action['tokens']} Green Tokens for {eco_action['action_name']}. Your sustainable farming practices are making a positive impact on the environment. Keep up the great work!"
                result["voice_summary"] = f"Congratulations! You earned {eco_action['tokens']} Green Tokens for {eco_action['action_name']}. Your eco-friendly farming is helping the planet."
            
            elif language == "hi":
                result["response_text"] = f"बधाई हो! आपने {eco_action['action_name']} के लिए {eco_action['tokens']} ग्रीन टोकन कमाए हैं। आपकी टिकाऊ खेती पर्यावरण पर सकारात्मक प्रभाव डाल रही है। शानदार काम जारी रखें!"
                result["voice_summary"] = f"बधाई हो! आपने {eco_action['action_name']} के लिए {eco_action['tokens']} ग्रीन टोकन कमाए। आपकी पर्यावरण अनुकूल खेती धरती की मदद कर रही है।"
            
            elif language == "mr":
                result["response_text"] = f"अभिनंदन! तुम्ही {eco_action['action_name']} साठी {eco_action['tokens']} ग्रीन टोकन मिळवले आहेत। तुमच्या शाश्वत शेती पद्धतींचा पर्यावरणावर सकारात्मक परिणाम होत आहे। उत्तम काम चालू ठेवा!"
                result["voice_summary"] = f"अभिनंदन! तुम्ही {eco_action['action_name']} साठी {eco_action['tokens']} ग्रीन टोकन मिळवले. तुमची पर्यावरण अनुकूल शेती पृथ्वीला मदत करत आहे."
            
            result["action_taken"] = f"Logged eco-action and awarded {eco_action['tokens']} tokens"
            return result
        
        # Detect regular intent
        intent = self._detect_intent(text_lower, language)
        result["intent"] = intent
        
        # Get appropriate response
        responses = self.responses.get(language, self.responses["en"])
        result["response_text"] = responses.get(intent, responses["unknown"])
        
        # Execute action based on intent
        if intent == "weather":
            from agents.weather_forecast_agent import WeatherForecastAgent
            weather_agent = WeatherForecastAgent()
            weather_data = weather_agent.predict_weather("Delhi", 24)
            
            # Use language-specific recommendations
            recs = weather_data.get("recommendations_multilingual", {}).get(language, weather_data.get("recommendations", []))
            
            result["data"] = {
                "summary": weather_data["summary"],
                "recommendations": recs[:2]
            }
            result["action_taken"] = "Fetched weather forecast"
        
        elif intent == "water":
            sensor_data = self.db.get_latest_sensor_data("FARM001", limit=1)
            if sensor_data:
                moisture = sensor_data[0].get("soil_moisture", 0)
                
                # Translate status based on language
                if language == "hi":
                    status = "अच्छा" if moisture > 40 else "कम"
                    recommendation = "सिंचाई की जरूरत है" if moisture < 40 else "पर्याप्त नमी है"
                elif language == "mr":
                    status = "चांगली" if moisture > 40 else "कमी"
                    recommendation = "सिंचनाची गरज आहे" if moisture < 40 else "पुरेसा ओलावा आहे"
                else:
                    status = "Good" if moisture > 40 else "Low"
                    recommendation = "Irrigation needed" if moisture < 40 else "Adequate moisture"
                
                result["data"] = {
                    "soil_moisture": moisture,
                    "status": status,
                    "recommendation": recommendation
                }
            result["action_taken"] = "Checked irrigation status"
        
        elif intent == "soil":
            sensor_data = self.db.get_latest_sensor_data("FARM001", limit=1)
            if sensor_data:
                # Translate status based on language
                if language == "hi":
                    status = "स्वस्थ"
                elif language == "mr":
                    status = "निरोगी"
                else:
                    status = "Healthy"
                
                result["data"] = {
                    "moisture": sensor_data[0].get("soil_moisture"),
                    "ph": sensor_data[0].get("soil_ph"),
                    "temperature": sensor_data[0].get("soil_temperature"),
                    "status": status
                }
            result["action_taken"] = "Analyzed soil health"
        
        elif intent == "disease":
            from agents.disease_detection_agent import DiseaseDetectionAgent
            disease_agent = DiseaseDetectionAgent()
            disease_data = disease_agent.detect_disease("wheat", [])
            
            # Translate status based on language
            if not disease_data["disease_detected"]:
                if language == "hi":
                    status = "स्वच्छ"
                elif language == "mr":
                    status = "स्वच्छ"
                else:
                    status = "Clear"
            else:
                if language == "hi":
                    status = "सतर्क"
                elif language == "mr":
                    status = "सतर्क"
                else:
                    status = "Alert"
            
            result["data"] = {
                "disease_detected": disease_data["disease_detected"],
                "status": status
            }
            result["action_taken"] = "Scanned for diseases"
        
        elif intent == "market":
            from agents.market_forecast_agent import MarketForecastAgent
            market_agent = MarketForecastAgent()
            
            try:
                market_data = market_agent.forecast_prices("wheat", 7)
                
                # Check if we got valid data (even fallback data is useful)
                if market_data and market_data.get("current_price"):
                    data_source = market_data.get("data_source", "")
                    is_live = "Live API" in data_source
                    
                    result["data"] = {
                        "current_price": market_data["current_price"],
                        "trend": market_data.get("trend", "stable"),
                        "recommendation": market_data["recommendations"][0] if market_data.get("recommendations") else "Hold",
                        "data_source": "Live API" if is_live else "Estimated",
                        "is_live": is_live
                    }
                    result["action_taken"] = "Fetched market prices" + (" (Live)" if is_live else " (Estimated)")
                else:
                    raise Exception("No market data available")
                    
            except Exception as e:
                print(f"⚠️ Market data error: {e}")
                # Show reasonable fallback message
                if language == "hi":
                    result["data"] = {
                        "current_price": "₹2,100-2,500",
                        "trend": "stable",
                        "recommendation": "Hold",
                        "data_source": "Estimated",
                        "is_live": False,
                        "note": "API अस्थायी रूप से अनुपलब्ध है"
                    }
                elif language == "mr":
                    result["data"] = {
                        "current_price": "₹2,100-2,500",
                        "trend": "stable",
                        "recommendation": "Hold",
                        "data_source": "Estimated",
                        "is_live": False,
                        "note": "API तात्पुरते अनुपलब्ध आहे"
                    }
                else:
                    result["data"] = {
                        "current_price": "₹2,100-2,500",
                        "trend": "stable",
                        "recommendation": "Hold",
                        "data_source": "Estimated",
                        "is_live": False,
                        "note": "API temporarily unavailable"
                    }
                result["action_taken"] = "Using estimated market prices"
        
        elif intent == "schemes":
            from agents.govt_scheme_agent import GovtSchemeAgent
            govt_agent = GovtSchemeAgent()
            schemes_data = govt_agent.get_applicable_schemes("all", "all")
            result["data"] = {
                "top_schemes": [s["name"] for s in schemes_data["priority_schemes"]],
                "helpline": schemes_data["application_support"]["helpline"]
            }
            result["action_taken"] = "Listed government schemes"
        
        # Generate voice-friendly summary
        result["voice_summary"] = self._generate_voice_summary(result, language)
        
        return result
    
    def _detect_intent(self, text: str, language: str) -> str:
        """Detect user intent from text"""
        
        commands = self.commands.get(language, self.commands["en"])
        
        for intent, keywords in commands.items():
            for keyword in keywords:
                if keyword in text:
                    return intent
        
        return "unknown"
    
    def _generate_voice_summary(self, result: Dict, language: str) -> str:
        """Generate concise voice response"""
        
        intent = result["intent"]
        data = result["data"]
        
        if language == "en":
            if intent == "weather":
                summary = data.get("summary", {})
                temp = summary.get('avg_temperature', 'N/A')
                rec = data.get('recommendations', ['Good day for farming'])[0]
                return f"The average temperature is {temp} degrees Celsius. {rec}"
            
            elif intent == "water":
                moisture = data.get('soil_moisture', 'N/A')
                rec = data.get('recommendation', '')
                return f"Soil moisture level is {moisture} percent. {rec}."
            
            elif intent == "soil":
                ph = data.get('ph', 'N/A')
                moisture = data.get('moisture', 'N/A')
                status = data.get('status', 'Unknown')
                return f"Soil pH is {ph} and moisture is {moisture} percent. Soil status: {status}."
            
            elif intent == "disease":
                status = data.get('status', 'Unknown')
                return f"Crop health status is {status}. No major diseases detected."
            
            elif intent == "market":
                # Check for API error
                if 'error' in data:
                    return data.get('message', 'Market data unavailable')
                
                price = data.get('current_price', 'N/A')
                trend = data.get('trend', 'stable')
                rec = data.get('recommendation', 'Hold')
                is_live = data.get('is_live', False)
                note = data.get('note', '')
                
                source_text = " from live API" if is_live else " (estimated range)"
                note_text = f" Note: {note}" if note else ""
                
                return f"Current wheat price is {price} rupees per quintal{source_text}. Market trend is {trend}. Recommendation: {rec}.{note_text}"
            
            elif intent == "schemes":
                schemes = data.get('top_schemes', [])
                helpline = data.get('helpline', 'N/A')
                if schemes:
                    return f"Top government schemes for you are: {', '.join(schemes[:2])}. For help, call {helpline}."
                return f"Several government schemes are available for farmers. Call helpline {helpline} for details."
        
        # Hindi summaries - COMPLETE NATIVE RESPONSES
        elif language == "hi":
            if intent == "weather":
                summary = data.get("summary", {})
                temp = summary.get('avg_temperature', 'N/A')
                recs = data.get('recommendations', ['खेती के लिए अच्छा दिन है'])
                return f"औसत तापमान {temp} डिग्री सेल्सियस है। {recs[0] if recs else 'मौसम अच्छा है।'}"
            
            elif intent == "water":
                moisture = data.get('soil_moisture', 'N/A')
                status = data.get('status', 'अच्छा')
                rec = data.get('recommendation', 'पानी की जरूरत नहीं')
                return f"मिट्टी में नमी {moisture} प्रतिशत है। स्थिति: {status}। {rec}।"
            
            elif intent == "soil":
                ph = data.get('ph', 'N/A')
                moisture = data.get('moisture', 'N/A')
                temp = data.get('temperature', 'N/A')
                return f"मिट्टी का पीएच {ph} है और नमी {moisture} प्रतिशत है। तापमान {temp} डिग्री है। मिट्टी स्वस्थ है।"
            
            elif intent == "disease":
                status = data.get('status', 'स्पष्ट')
                if status == "Clear" or status == "स्पष्ट":
                    return "फसल की जांच पूरी हुई। कोई बड़ी बीमारी नहीं मिली। फसल स्वस्थ है।"
                else:
                    return f"फसल की स्थिति: {status}। कृपया ध्यान दें।"
            
            elif intent == "market":
                # Check for API error
                if 'error' in data:
                    return data.get('message', 'बाजार डेटा उपलब्ध नहीं है')
                
                price = data.get('current_price', 'N/A')
                trend = data.get('trend', 'stable')
                trend_hi = {'stable': 'स्थिर', 'rising': 'बढ़ रहा', 'falling': 'गिर रहा'}.get(trend, trend)
                rec = data.get('recommendation', 'Hold')
                rec_hi = {'Hold': 'रुकें', 'Sell': 'बेचें', 'Wait': 'प्रतीक्षा करें'}.get(rec, rec)
                is_live = data.get('is_live', False)
                note = data.get('note', '')
                
                source_text = " लाइव API से" if is_live else " (अनुमानित रेंज)"
                note_text = f" नोट: {note}" if note else ""
                
                return f"गेहूं का वर्तमान भाव {price} रुपये प्रति क्विंटल है{source_text}। बाजार का रुझान {trend_hi} है। सुझाव: {rec_hi}।{note_text}"
            
            elif intent == "schemes":
                schemes = data.get('top_schemes', [])
                helpline = data.get('helpline', 'N/A')
                if schemes and len(schemes) >= 2:
                    return f"आपके लिए प्रमुख सरकारी योजनाएं: {schemes[0]} और {schemes[1]}। सहायता के लिए हेल्पलाइन {helpline} पर कॉल करें।"
                elif schemes and len(schemes) == 1:
                    return f"आपके लिए प्रमुख योजना: {schemes[0]}। अधिक जानकारी के लिए {helpline} पर कॉल करें।"
                return f"किसानों के लिए कई सरकारी योजनाएं उपलब्ध हैं। विवरण के लिए हेल्पलाइन {helpline} पर कॉल करें।"
            
            elif intent == "unknown":
                return "मुझे समझ नहीं आया। कृपया पूछें: मौसम, पानी, मिट्टी, बीमारी, बाजार, या योजना के बारे में।"
        
        # Marathi summaries - COMPLETE NATIVE RESPONSES
        elif language == "mr":
            if intent == "weather":
                summary = data.get("summary", {})
                temp = summary.get('avg_temperature', 'N/A')
                recs = data.get('recommendations', ['शेतीसाठी चांगला दिवस आहे'])
                return f"सरासरी तापमान {temp} अंश सेल्सिअस आहे। {recs[0] if recs else 'हवामान चांगले आहे।'}"
            
            elif intent == "water":
                moisture = data.get('soil_moisture', 'N/A')
                status = data.get('status', 'चांगली')
                rec = data.get('recommendation', 'पाण्याची गरज नाही')
                rec_mr = {'Irrigation needed': 'सिंचनाची गरज आहे', 
                         'Adequate moisture': 'पुरेसा ओलावा आहे',
                         'Water soon': 'लवकरच पाणी द्या'}.get(rec, rec)
                return f"मातीत ओलावा {moisture} टक्के आहे। स्थिती: {status}। {rec_mr}।"
            
            elif intent == "soil":
                ph = data.get('ph', 'N/A')
                moisture = data.get('moisture', 'N/A')
                temp = data.get('temperature', 'N/A')
                status = data.get('status', 'निरोगी')
                return f"मातीचा पीएच {ph} आहे आणि ओलावा {moisture} टक्के आहे। तापमान {temp} अंश आहे। माती {status} आहे।"
            
            elif intent == "disease":
                status = data.get('status', 'स्वच्छ')
                if status == "Clear" or status == "स्वच्छ":
                    return "पिकाची तपासणी पूर्ण झाली. कोणताही मोठा रोग आढळला नाही. पीक निरोगी आहे."
                else:
                    return f"पिकाची आरोग्य स्थिती: {status}. कृपया लक्ष द्या."
            
            elif intent == "market":
                # Check for API error
                if 'error' in data:
                    return data.get('message', 'बाजार डेटा उपलब्ध नाही')
                
                price = data.get('current_price', 'N/A')
                trend = data.get('trend', 'stable')
                trend_mr = {'stable': 'स्थिर', 'rising': 'वाढत आहे', 'falling': 'घटत आहे'}.get(trend, trend)
                rec = data.get('recommendation', 'Hold')
                rec_mr = {'Hold': 'थांबा', 'Sell': 'विका', 'Wait': 'प्रतीक्षा करा'}.get(rec, rec)
                is_live = data.get('is_live', False)
                note = data.get('note', '')
                
                source_text = " लाइव्ह API वरून" if is_live else " (अंदाजे रेंज)"
                note_text = f" नोंद: {note}" if note else ""
                
                return f"गव्हाची सध्याची किंमत {price} रुपये प्रति क्विंटल आहे{source_text}। बाजार ट्रेंड {trend_mr} आहे। सल्ला: {rec_mr}।{note_text}"
            
            elif intent == "schemes":
                schemes = data.get('top_schemes', [])
                helpline = data.get('helpline', 'N/A')
                if schemes and len(schemes) >= 2:
                    return f"तुमच्यासाठी प्रमुख सरकारी योजना: {schemes[0]} आणि {schemes[1]}. मदतीसाठी हेल्पलाइन {helpline} वर कॉल करा."
                elif schemes and len(schemes) == 1:
                    return f"तुमच्यासाठी प्रमुख योजना: {schemes[0]}. अधिक माहितीसाठी {helpline} वर कॉल करा."
                return f"शेतकऱ्यांसाठी अनेक सरकारी योजना उपलब्ध आहेत. तपशीलासाठी हेल्पलाइन {helpline} वर कॉल करा."
            
            elif intent == "unknown":
                return "मला समजले नाही. कृपया विचारा: हवामान, पाणी, माती, रोग, बाजार, किंवा योजना बद्दल."
        
        return result["response_text"]
    
    def _detect_eco_action(self, text: str, language: str) -> Dict[str, Any]:
        """Detect eco-friendly actions from text and return action details"""
        
        # Define eco-actions with multilingual keywords and token rewards
        eco_actions = {
            "drip_irrigation": {
                "keywords": {
                    "en": ["drip irrigation", "drip irrigate", "installed drip", "use drip", "using drip", "setup drip"],
                    "hi": ["drip sinchai", "drip irrigation", "थेंब सिंचाई", "थेंब सिंचन"],
                    "mr": ["थेंब सिंचन", "ड्रिप सिंचन", "drip irrigation", "थेंब पाणी"]
                },
                "tokens": 20,
                "action_name": {
                    "en": "Drip Irrigation",
                    "hi": "थेंब सिंचाई",
                    "mr": "थेंब सिंचन"
                }
            },
            "organic_fertilizer": {
                "keywords": {
                    "en": ["organic fertilizer", "organic compost", "organic manure", "bio fertilizer", "vermicompost", "applied organic", "use organic"],
                    "hi": ["organic khad", "jaivic khad", "जैविक खाद", "कम्पोस्ट खाद"],
                    "mr": ["जैविक खत", "सेंद्रिय खत", "कंपोस्ट", "organic khate"]
                },
                "tokens": 15,
                "action_name": {
                    "en": "Organic Fertilizer",
                    "hi": "जैविक खाद",
                    "mr": "जैविक खत"
                }
            },
            "solar_pump": {
                "keywords": {
                    "en": ["solar pump", "solar water pump", "solar powered pump", "installed solar pump"],
                    "hi": ["solar pump", "सौर पंप", "solar pani pump"],
                    "mr": ["सौर पंप", "solar pump", "सोलर पंप"]
                },
                "tokens": 30,
                "action_name": {
                    "en": "Solar Pump",
                    "hi": "सौर पंप",
                    "mr": "सौर पंप"
                }
            },
            "rainwater_harvesting": {
                "keywords": {
                    "en": ["rainwater harvest", "rain water collection", "collect rainwater", "rainwater tank"],
                    "hi": ["varshe ka pani", "बारिश का पानी संग्रहण", "rainwater harvest"],
                    "mr": ["पावसाचे पाणी", "पावसाचे पाणी संचयन", "rainwater harvest"]
                },
                "tokens": 25,
                "action_name": {
                    "en": "Rainwater Harvesting",
                    "hi": "वर्षा जल संचयन",
                    "mr": "पावसाचे पाणी संचयन"
                }
            },
            "composting": {
                "keywords": {
                    "en": ["composting", "compost pit", "started compost", "making compost", "compost bin"],
                    "hi": ["compost", "khad banana", "कम्पोस्ट बनाना"],
                    "mr": ["कंपोस्ट", "खत तयार", "composting"]
                },
                "tokens": 15,
                "action_name": {
                    "en": "Composting",
                    "hi": "कम्पोस्टिंग",
                    "mr": "कंपोस्टिंग"
                }
            },
            "crop_rotation": {
                "keywords": {
                    "en": ["crop rotation", "rotate crops", "rotated crop", "crop cycle"],
                    "hi": ["fasal chakra", "फसल चक्र", "crop rotation"],
                    "mr": ["पीक फेरबदल", "फसल चक्र", "crop rotation"]
                },
                "tokens": 12,
                "action_name": {
                    "en": "Crop Rotation",
                    "hi": "फसल चक्र",
                    "mr": "पीक फेरबदल"
                }
            },
            "mulching": {
                "keywords": {
                    "en": ["mulching", "applied mulch", "mulch cover", "mulch layer"],
                    "hi": ["mulching", "mulch dalana", "मल्चिंग"],
                    "mr": ["mulching", "मल्चिंग", "झाकण"]
                },
                "tokens": 10,
                "action_name": {
                    "en": "Mulching",
                    "hi": "मल्चिंग",
                    "mr": "मल्चिंग"
                }
            },
            "zero_tillage": {
                "keywords": {
                    "en": ["zero tillage", "no till", "no tillage", "conservation tillage"],
                    "hi": ["zero tillage", "bina jotai", "बिना जोताई"],
                    "mr": ["zero tillage", "शून्य नांगरणी"]
                },
                "tokens": 18,
                "action_name": {
                    "en": "Zero Tillage",
                    "hi": "बिना जोताई",
                    "mr": "शून्य नांगरणी"
                }
            },
            "integrated_pest_management": {
                "keywords": {
                    "en": ["ipm", "integrated pest", "bio pesticide", "organic pest control"],
                    "hi": ["ipm", "jaivik keetnashak", "जैविक कीटनाशक"],
                    "mr": ["ipm", "जैविक कीटकनाशक", "एकात्मिक"]
                },
                "tokens": 20,
                "action_name": {
                    "en": "Integrated Pest Management",
                    "hi": "एकीकृत कीट प्रबंधन",
                    "mr": "एकात्मिक कीटक व्यवस्थापन"
                }
            },
            "smart_irrigation": {
                "keywords": {
                    "en": ["smart irrigation", "automated irrigation", "sensor irrigation"],
                    "hi": ["smart sinchai", "स्मार्ट सिंचाई"],
                    "mr": ["स्मार्ट सिंचन", "smart irrigation"]
                },
                "tokens": 10,
                "action_name": {
                    "en": "Smart Irrigation",
                    "hi": "स्मार्ट सिंचाई",
                    "mr": "स्मार्ट सिंचन"
                }
            }
        }
        
        # Check each eco-action
        for action_type, action_data in eco_actions.items():
            keywords = action_data["keywords"].get(language, action_data["keywords"]["en"])
            
            for keyword in keywords:
                if keyword in text:
                    return {
                        "action_type": action_type,
                        "action_name": action_data["action_name"].get(language, action_data["action_name"]["en"]),
                        "tokens": action_data["tokens"]
                    }
        
        return None
    
    def _log_to_blockchain(self, eco_action: Dict, language: str) -> Dict[str, Any]:
        """Log eco-action to blockchain and actions_log database"""
        try:
            from agents.blockchain_agent import BlockchainAgent
            from core.database import Database
            
            blockchain_agent = BlockchainAgent()
            db = Database()
            farm_id = "FARM001"  # Default farm ID
            
            # Add transaction to blockchain
            result = blockchain_agent.add_transaction(
                farm_id=farm_id,
                action_type=eco_action["action_type"],
                action_details=eco_action["action_name"],
                green_tokens=eco_action["tokens"]
            )
            
            # Also log to actions_log table
            try:
                db.log_action(
                    farm_id=farm_id,
                    action_type=eco_action["action_type"],
                    action_details=f"Voice command: {eco_action['action_name']}",
                    green_tokens=eco_action["tokens"]
                )
            except Exception as db_error:
                print(f"Warning: Failed to log action to database: {db_error}")
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "block_index": result["block_index"],
                    "tokens_earned": result["tokens_earned"],
                    "new_balance": result["new_balance"],
                    "farm_id": farm_id
                }
            else:
                return {"success": False, "error": "Blockchain logging failed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _detect_language(self, text: str) -> str:
        """Auto-detect language from text based on character scripts"""
        # Check for Devanagari script (Hindi/Marathi)
        devanagari_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "en"  # Default to English
        
        devanagari_ratio = devanagari_chars / total_chars if total_chars > 0 else 0
        
        # If more than 30% Devanagari, determine if Hindi or Marathi
        if devanagari_ratio > 0.3:
            text_lower = text.lower()
            
            # Marathi-specific words/patterns
            marathi_indicators = ['आहे', 'आहेत', 'काय', 'कशी', 'तुम्ही', 'माती', 'पाऊस', 'मदत']
            marathi_count = sum(1 for word in marathi_indicators if word in text)
            
            # Hindi-specific words/patterns
            hindi_indicators = ['है', 'हैं', 'क्या', 'कैसे', 'आप', 'मिट्टी', 'बारिश', 'मदद']
            hindi_count = sum(1 for word in hindi_indicators if word in text)
            
            # Return based on indicator count
            if marathi_count > hindi_count:
                return "mr"
            elif hindi_count > marathi_count:
                return "hi"
            else:
                # Default to Hindi if unclear
                return "hi"
        
        # Check for common Hindi/Marathi romanized words
        text_lower = text.lower()
        
        marathi_roman = ['hava', 'paus', 'maati', 'kashi', 'tumhi', 'mala']
        marathi_roman_count = sum(1 for word in marathi_roman if word in text_lower)
        
        hindi_roman = ['mausam', 'barish', 'mitti', 'kaise', 'aap', 'mujhe']
        hindi_roman_count = sum(1 for word in hindi_roman if word in text_lower)
        
        if marathi_roman_count > hindi_roman_count and marathi_roman_count > 0:
            return "mr"
        elif hindi_roman_count > 0:
            return "hi"
        
        # Default to English
        return "en"
