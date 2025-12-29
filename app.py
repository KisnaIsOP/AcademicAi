from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import random
import re
from datetime import datetime
import threading
import time
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
loaded = load_dotenv(env_path)
print(f"DEBUG: Loading .env from {env_path}")
print(f"DEBUG: .env loaded: {loaded}")
print(f"DEBUG: API Key present: {bool(os.getenv('OPENROUTER_API_KEY'))}")
if os.getenv('OPENROUTER_API_KEY'):
    print(f"DEBUG: API Key starts with: {os.getenv('OPENROUTER_API_KEY')[:10]}...")


# Configure OpenRouter (OpenAI Compatible)
try:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("No API key found in environment variables")
        # We don't raise here to allow the app to start, but it will fail on generation
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    logger.info("OpenRouter client successfully configured")
except Exception as e:
    logger.error(f"OpenRouter Configuration Error: {e}", exc_info=True)
    client = None

app = Flask(__name__)

# Global storage for sessions (in-memory)
# Format: {session_id: [{"role": "user", "content": "..."}, ...]}
sessions = {}

# AI Configuration
AI_DESCRIPTION = """
You are Hecker, an advanced AI learning companion designed to provide personalized, context-aware educational support. 
Your goal is to help students learn effectively by:
1. Breaking down complex topics into digestible explanations
2. Providing adaptive learning strategies
3. Generating targeted study materials
4. Offering motivational and constructive feedback

Key Characteristics:
- Patient and encouraging
- Adaptable to different learning styles
- Capable of explaining topics at various complexity levels
- Focused on student's individual learning journey
"""

# Model Configuration - Prioritizing high capability free models
MODELS = [
    "google/gemma-2-9b-it:free",                 # User preferred model
    "google/gemini-2.0-flash-thinking-exp:free", # High reasoning capability
    "meta-llama/llama-3.1-70b-instruct:free",    # Excellent general knowledge
    "meta-llama/llama-3.1-8b-instruct:free",     # Fast and reliable fallback
    "microsoft/phi-3-mini-128k-instruct:free",   # Very reliable & fast fallback
    "mistralai/mistral-7b-instruct:free",        # Solid fallback
]

def generate_with_fallback(messages, temperature=0.7):
    """Try to generate a response using models in priority order"""
    last_error = None
    
    logger.debug(f"Generating with messages: {messages}")

    for model in MODELS:
        try:
            logger.info(f"Attempting generation with model: {model}")
            if not client:
                raise ValueError("OpenRouter client not initialized")

            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=0.9,
                max_tokens=2048,
                extra_headers={
                    "HTTP-Referer": "http://localhost:5000", # Optional, for including your app on openrouter.ai rankings.
                    "X-Title": "AcademicAi", # Optional. Shows in rankings on openrouter.ai.
                }
            )
            
            content = completion.choices[0].message.content
            if not content:
                logger.warning(f"Model {model} returned empty content")
                continue
                
            logger.debug(f"Generation success with {model}: {content[:50]}...")
            return content
            
        except Exception as e:
            logger.warning(f"Model {model} failed: {str(e)}")
            last_error = e
            continue
            
    raise last_error

@app.route('/generate_response', methods=['POST'])
def generate_response():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    # Initialize session if not exists
    if session_id not in sessions:
        sessions[session_id] = [
            {"role": "system", "content": AI_DESCRIPTION}
        ]
    
    # Add user message to history
    sessions[session_id].append({"role": "user", "content": user_message})
    
    try:
        response_text = generate_with_fallback(sessions[session_id])
        
        # Add AI response to history
        sessions[session_id].append({"role": "assistant", "content": response_text})
        
        return jsonify({
            'response': response_text,
            'timestamp': datetime.now().strftime("%I:%M %p")
        })
    except Exception as e:
        logger.error(f"Generation Error: {e}")
        return jsonify({
            'response': f"I'm experiencing difficulties with all available models. Please try again later. Error: {str(e)}",
            'timestamp': datetime.now().strftime("%I:%M %p")
        })

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.json
        query_text = data.get('query', '')
        # is_regeneration = data.get('regenerate', False) # Unused currently

        # Generate response
        response_text = generate_response_with_context(query_text)

        # Update conversation context
        conversation_context.add_interaction(query_text, response_text)

        return jsonify({
            'success': True,
            'response': response_text
        })

    except Exception as e:
        app.logger.error(f"Query processing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_response_with_context(query):
    """Generate a response that considers conversation context and provides detailed, step-by-step explanations"""
    
    # Special handling for dimensional analysis and scientific queries
    if any(keyword in query.lower() for keyword in ['dimension', 'dimensional analysis', 'viscosity', 'prove', 'derivation']):
        response = """😮‍💨 💗 Dimensional Analysis of Viscosity

**Step 1: Define the Physical Quantity**
Viscosity (η) is a measure of a fluid's resistance to flow, defined as the ratio of shear stress to shear rate.

**Symbolic Representation:**
η = τ / γ̇

**Step 2: Dimensional Analysis of Components**
- Shear Stress (τ): Force per unit area
  * Dimensions: [M L T^-2] / [L^2] = [M L^-1 T^-2]
- Shear Rate (γ̇): Velocity gradient
  * Dimensions: [L T^-1] / [L] = [T^-1]

**Step 3: Dimensional Consistency**
Combining the dimensions:
[τ / γ̇] = [M L^-1 T^-2] / [T^-1] = [M L^-1 T^-1]

**Step 4: Physical Interpretation**
The dimensional analysis confirms that viscosity has consistent units:
- Mass per length per time
- Typically expressed in Pascal-seconds (Pa·s)

**Key Insights:**
- Viscosity quantifies a fluid's internal resistance to flow
- Dimensional analysis validates the physical meaning of the quantity
"""
        return format_mathematical_notation(response)

    # Default response generation logic
    context_prompt = f"""Context:
- Current Query: {query}
- Conversation History: {len(conversation_context.history)} previous interactions

Guidelines:
1. Provide a clear, comprehensive response
2. Break down complex topics into digestible steps
3. Use engaging and accessible language
4. Include practical examples or real-world applications
5. Use standard mathematical notation for equations

Query: {query}
"""

    try:
        response = generate_with_fallback([
            {"role": "system", "content": AI_DESCRIPTION},
            {"role": "user", "content": context_prompt}
        ])
        
        # Apply mathematical notation formatting to the response
        formatted_response = format_mathematical_notation(response)
        return sanitize_response(formatted_response)
    except Exception as e:
        app.logger.error(f"Response generation error: {e}")
        return f"I'm sorry, I encountered an error processing your query. {generate_emoji()}"

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.json
        score = data.get('score')
        feedback_text = data.get('feedback')
        logger.info(f"Feedback received - Score: {score}, Text: {feedback_text}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 Error: {request.url}")
    return render_template('index.html', now=datetime.now().strftime("%I:%M %p"), initial_question="Page not found, but I'm here to help!"), 404

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'alive'}), 200

if __name__ == '__main__':
    app.run(debug=True)
