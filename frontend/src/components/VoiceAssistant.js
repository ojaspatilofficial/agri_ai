import React, { useState } from 'react';
import axios from 'axios';

function VoiceAssistant({ apiUrl }) {
  const [isListening, setIsListening] = useState(false);
  const [response, setResponse] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showInputModal, setShowInputModal] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [language, setLanguage] = useState('en');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);

  const handleVoiceCommand = async (text) => {
    try {
      const res = await axios.post(`${apiUrl}/voice_command`, {
        text: text,
        language: language
      });
      
      const responseText = res.data.voice_summary || res.data.response_text;
      setResponse(responseText);
      setShowModal(true);
      
      // Speak response with multilingual support
      await speakText(responseText, language);
    } catch (error) {
      console.error('Error processing voice command:', error);
      setResponse('Sorry, I could not process your request.');
      setShowModal(true);
    }
  };

  // Enhanced Multilingual Text-to-Speech Function
  const speakText = async (text, lang) => {
    try {
      // Stop any ongoing speech
      stopSpeech();
      setIsSpeaking(true);

      console.log('🔊 Starting TTS for text:', text.substring(0, 50) + '...');
      console.log('🌐 Language:', lang);

      // Method 1: Try backend gTTS (better for Hindi/Marathi)
      try {
        console.log('📡 Attempting backend gTTS...');
        const audioResponse = await axios.post(
          `${apiUrl}/text_to_speech`,
          null,
          {
            params: { text, language: lang },
            responseType: 'blob',
            timeout: 10000 // 10 second timeout
          }
        );
        
        console.log('✅ Backend TTS response received, size:', audioResponse.data.size, 'bytes');
        
        // Play audio from backend
        const audioBlob = new Blob([audioResponse.data], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        // Set volume to maximum
        audio.volume = 1.0;
        
        setCurrentAudio(audio);
        
        audio.onloadedmetadata = () => {
          console.log('🎵 Audio loaded, duration:', audio.duration, 'seconds');
        };
        
        audio.onplay = () => {
          console.log('▶️ Audio started playing');
        };
        
        audio.onended = () => {
          console.log('⏹️ Audio finished playing');
          URL.revokeObjectURL(audioUrl);
          setIsSpeaking(false);
          setCurrentAudio(null);
        };
        
        audio.onerror = (e) => {
          console.error('❌ Audio playback error:', e);
          console.error('Audio error details:', audio.error);
          URL.revokeObjectURL(audioUrl);
          setIsSpeaking(false);
          setCurrentAudio(null);
          
          // Try browser fallback on audio error
          throw new Error('Audio playback failed');
        };
        
        try {
          console.log('🎬 Attempting to play audio...');
          const playPromise = audio.play();
          
          if (playPromise !== undefined) {
            await playPromise;
            console.log('✅ Audio playing successfully');
          }
        } catch (playError) {
          console.error('❌ Play failed:', playError);
          console.error('This might be due to browser autoplay policy');
          
          // Show alert to user
          alert('Please click the "Replay" button to hear the response. Browser blocked autoplay.');
          setIsSpeaking(false);
          
          // Keep audio available for manual replay
          return;
        }
        
        return; // Exit if backend TTS works
      } catch (backendError) {
        console.warn('⚠️ Backend TTS failed:', backendError.message);
        console.log('🔄 Falling back to browser Web Speech API...');
      }

      // Method 2: Fallback to browser Web Speech API
      if ('speechSynthesis' in window) {
        console.log('🗣️ Using browser Web Speech API');
        
        // Load voices if not loaded
        const voices = window.speechSynthesis.getVoices();
        if (voices.length === 0) {
          console.log('⏳ Waiting for voices to load...');
          await new Promise(resolve => {
            window.speechSynthesis.onvoiceschanged = () => resolve();
            setTimeout(resolve, 1000); // Timeout after 1 second
          });
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set language with proper locale codes
        const langMap = {
          'hi': 'hi-IN',
          'mr': 'mr-IN',
          'en': 'en-US'
        };
        utterance.lang = langMap[lang] || 'en-US';
        
        // Configure voice parameters
        utterance.rate = 0.9; // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Try to find native voice for the language
        const loadedVoices = window.speechSynthesis.getVoices();
        console.log('📢 Available voices:', loadedVoices.length);
        
        const nativeVoice = loadedVoices.find(voice => 
          voice.lang.startsWith(lang) || voice.lang.startsWith(langMap[lang])
        );
        
        if (nativeVoice) {
          utterance.voice = nativeVoice;
          console.log('✅ Using voice:', nativeVoice.name, '(' + nativeVoice.lang + ')');
        } else {
          console.log('⚠️ No native voice found for', lang, 'using default');
        }
        
        // Speak with error handling
        return new Promise((resolve, reject) => {
          utterance.onstart = () => {
            console.log('▶️ Browser TTS started');
          };
          
          utterance.onend = () => {
            console.log('✅ Browser TTS finished');
            setIsSpeaking(false);
            resolve();
          };
          
          utterance.onerror = (event) => {
            console.error('❌ Browser TTS error:', event);
            setIsSpeaking(false);
            reject(event);
          };
          
          console.log('🎬 Speaking with browser TTS...');
          window.speechSynthesis.speak(utterance);
        });
      } else {
        console.error('❌ Speech Synthesis not supported in this browser');
        setIsSpeaking(false);
      }
    } catch (error) {
      console.error('❌ Text-to-speech error:', error);
      setIsSpeaking(false);
      // Silent fail - don't disrupt user experience
    }
  };

  // Stop speech function
  const stopSpeech = () => {
    // Stop audio playback
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setCurrentAudio(null);
    }
    
    // Stop browser speech synthesis
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    
    setIsSpeaking(false);
  };

  // Replay speech function
  const replaySpeech = () => {
    if (response) {
      speakText(response, language);
    }
  };

  const handleClick = () => {
    setIsListening(true);
    
    // Check if browser supports speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.lang = language === 'hi' ? 'hi-IN' : language === 'mr' ? 'mr-IN' : 'en-US';
      recognition.continuous = false;
      recognition.interimResults = false;
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Heard:', transcript);
        handleVoiceCommand(transcript);
        setIsListening(false);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setResponse('Voice recognition error. Please try typing your command.');
        setShowModal(true);
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      recognition.start();
    } else {
      // Fallback: show input modal
      const command = prompt('Voice recognition not supported. Please type your command:\n(Try: weather, irrigation, soil, disease, market, schemes, report)');
      if (command) {
        handleVoiceCommand(command);
      }
      setIsListening(false);
    }
  };

  const handleTextSubmit = () => {
    if (textInput.trim()) {
      handleVoiceCommand(textInput);
      setTextInput('');
      setShowInputModal(false);
    }
  };

  return (
    <>
      {/* Voice Button */}
      <button 
        className={`voice-assistant ${isListening ? 'active' : ''}`}
        onClick={handleClick}
        title="Voice Assistant (Click to speak)"
        style={{ marginRight: '1rem' }}
      >
        🎤
      </button>

      {/* Text Input Button */}
      <button 
        className="voice-assistant"
        onClick={() => setShowInputModal(true)}
        title="Type Command"
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          fontSize: '1.5rem',
          cursor: 'pointer',
          boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          zIndex: 1000,
          transition: 'transform 0.2s'
        }}
        onMouseOver={(e) => e.target.style.transform = 'scale(1.1)'}
        onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
      >
        ⌨️
      </button>

      {/* Text Input Modal */}
      {showInputModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }} onClick={() => setShowInputModal(false)}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '2rem',
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              ⌨️ Type Your Command
            </h3>
            
            {/* Language Selector */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ marginRight: '1rem', fontWeight: '500' }}>Language:</label>
              <select 
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{ 
                  padding: '0.5rem', 
                  borderRadius: '4px', 
                  border: '1px solid #e5e7eb',
                  fontSize: '1rem'
                }}
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="mr">मराठी (Marathi)</option>
              </select>
            </div>
            
            {/* Text Input */}
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type your question... (e.g., What's the weather?)"
              style={{
                width: '100%',
                minHeight: '100px',
                padding: '1rem',
                borderRadius: '8px',
                border: '2px solid #e5e7eb',
                fontSize: '1rem',
                marginBottom: '1rem',
                resize: 'vertical',
                fontFamily: 'inherit'
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleTextSubmit();
                }
              }}
            />
            
            {/* Buttons */}
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                className="btn btn-secondary"
                onClick={() => {
                  setShowInputModal(false);
                  setTextInput('');
                }}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleTextSubmit}
                style={{ flex: 1 }}
                disabled={!textInput.trim()}
              >
                Send 📤
              </button>
            </div>
            
            {/* Quick Commands */}
            <div style={{ 
              marginTop: '1rem', 
              padding: '0.75rem', 
              background: '#f0fdf4', 
              borderRadius: '8px',
              fontSize: '0.875rem'
            }}>
              <strong>Quick Commands:</strong>
              <div style={{ 
                display: 'flex', 
                flexWrap: 'wrap', 
                gap: '0.5rem', 
                marginTop: '0.5rem' 
              }}>
                <button 
                  onClick={() => setTextInput("What's the weather?")}
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #10b981',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '0.75rem'
                  }}
                >
                  Weather
                </button>
                <button 
                  onClick={() => setTextInput("Check soil moisture")}
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #10b981',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '0.75rem'
                  }}
                >
                  Soil
                </button>
                <button 
                  onClick={() => setTextInput("Market prices")}
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #10b981',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '0.75rem'
                  }}
                >
                  Market
                </button>
                <button 
                  onClick={() => setTextInput("Government schemes")}
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #10b981',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '0.75rem'
                  }}
                >
                  Schemes
                </button>
                <button 
                  onClick={() => setTextInput("Give me a farm report")}
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #10b981',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '0.75rem'
                  }}
                >
                  Farm Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Response Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }} onClick={() => setShowModal(false)}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '2rem',
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              🤖 AI Assistant Response
            </h3>
            
            {/* Language Selector */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ marginRight: '1rem' }}>Language:</label>
              <select 
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #e5e7eb' }}
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="mr">मराठी (Marathi)</option>
              </select>
            </div>
            
            <p style={{ 
              background: '#f9fafb', 
              padding: '1rem', 
              borderRadius: '8px', 
              marginBottom: '1rem',
              lineHeight: '1.6'
            }}>
              {response}
            </p>
            
            {/* TTS Controls */}
            <div style={{ 
              display: 'flex', 
              gap: '0.5rem', 
              marginBottom: '1rem',
              justifyContent: 'center'
            }}>
              <button
                onClick={replaySpeech}
                disabled={isSpeaking}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  border: '1px solid #10b981',
                  background: isSpeaking ? '#e5e7eb' : 'white',
                  cursor: isSpeaking ? 'not-allowed' : 'pointer',
                  fontSize: '0.875rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                🔊 {isSpeaking ? 'Speaking...' : 'Replay'}
              </button>
              
              {isSpeaking && (
                <button
                  onClick={stopSpeech}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    border: '1px solid #ef4444',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}
                >
                  ⏹️ Stop
                </button>
              )}
            </div>
            
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                className="btn btn-primary"
                onClick={() => {
                  stopSpeech();
                  setShowModal(false);
                }}
                style={{ flex: 1 }}
              >
                Close
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => {
                  stopSpeech();
                  handleClick();
                }}
                style={{ flex: 1 }}
              >
                🎤 Ask Again
              </button>
            </div>
            
            <div style={{ 
              marginTop: '1rem', 
              padding: '0.75rem', 
              background: '#f0fdf4', 
              borderRadius: '8px',
              fontSize: '0.875rem'
            }}>
              <strong>Try asking:</strong>
              <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                <li>What's the weather?</li>
                <li>Check soil moisture</li>
                <li>Market prices</li>
                <li>Government schemes</li>
                <li>Give me a farm report</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default VoiceAssistant;
