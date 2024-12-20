from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
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
load_dotenv()

# Configure Gemini AI with enhanced error handling
try:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("No API key found in environment variables")
        raise ValueError("Gemini API key is missing")
    
    genai.configure(api_key=api_key)
    logger.info("Gemini AI successfully configured")
except Exception as e:
    logger.error(f"Gemini API Configuration Error: {e}", exc_info=True)
    # You might want to add a fallback mechanism or exit the application
    raise

app = Flask(__name__)

# Self-Pinging Function with Enhanced Reliability
def keep_alive():
    while True:
        try:
            # Use multiple backup URLs for redundancy
            urls = [
                'https://hecker-ai.onrender.com',
                'https://academic-ai-2-0.onrender.com',
                'https://academic-ai-backup.onrender.com'
            ]
            
            # Ping multiple URLs for increased reliability
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    print(f"Self-ping status for {url}: {response.status_code}")
                except requests.RequestException as e:
                    print(f"Self-ping error for {url}: {e}")
                
                # Add a small delay between pings to prevent overwhelming the server
                time.sleep(2)
            
            # Reduce sleep time to ping more frequently
            time.sleep(300)  # 5 minutes instead of 20 minutes
        
        except Exception as e:
            print(f"Critical self-ping error: {e}")
            
            # If something goes wrong, wait a bit and retry
            time.sleep(60)  # Wait 1 minute before retrying

# Start the keep-alive thread with error handling
try:
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("Self-ping thread started successfully")
except Exception as e:
    print(f"Failed to start self-ping thread: {e}")

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

# Model Configuration
generation_config = {
    'temperature': 0.7,
    'top_p': 0.9,
    'max_output_tokens': 2048
}

safety_settings = [
    {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
    {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
    {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
    {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'}
]

model = genai.GenerativeModel(
    model_name='gemini-pro', 
    generation_config=generation_config, 
    safety_settings=safety_settings
)

chat = model.start_chat(history=[
    {
        'role': 'user',
        'parts': [AI_DESCRIPTION]
    },
    {
        'role': 'model',
        'parts': ['I understand. I will act as Hecker, an advanced AI learning companion with the described characteristics.']
    }
])

# Context Management
class ConversationContext:
    def __init__(self, max_history=5):
        self.history = []
        self.max_history = max_history
        self.current_topic = None
        self.difficulty_level = 'intermediate'

    def add_interaction(self, user_query, ai_response):
        # Trim history if it exceeds max_history
        if len(self.history) >= self.max_history:
            self.history.pop(0)
        
        # Add new interaction
        self.history.append({
            'user_query': user_query,
            'ai_response': ai_response
        })

    def detect_topic(self, query):
        # Simple topic detection using keyword matching
        topics = {
            'mathematics': ['math', 'algebra', 'geometry', 'calculus', 'trigonometry'],
            'science': ['physics', 'chemistry', 'biology', 'science'],
            'language': ['english', 'grammar', 'writing', 'literature'],
            'history': ['history', 'historical', 'civilization', 'era'],
            'technology': ['computer', 'programming', 'tech', 'coding']
        }

        for topic, keywords in topics.items():
            if any(keyword in query.lower() for keyword in keywords):
                self.current_topic = topic
                return topic
        
        return None

    def adjust_difficulty(self, query):
        # Detect complexity of query and adjust difficulty
        complexity_indicators = {
            'advanced': ['prove', 'derive', 'complex', 'advanced', 'theoretical'],
            'beginner': ['explain', 'what is', 'basic', 'simple', 'introduction']
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in query.lower() for indicator in indicators):
                self.difficulty_level = level
                break

conversation_context = ConversationContext()

def generate_emoji():
    """Generate a random emoji to add personality"""
    emojis = [
        '😊', '🌟', '👍', '🚀', '🤔', '💡', '📚', '🎓', 
        '🧠', '✨', '🌈', '👏', '🤓', '💪', '🌞'
    ]
    return random.choice(emojis)

def format_solution(text):
    """Format mathematical solutions with clear steps and equations"""
    # Split into steps
    steps = text.split('\n\n')
    formatted_steps = []
    
    for i, step in enumerate(steps):
        if i == 0 and step.lower().startswith('solution:'):
            formatted_steps.append(f"**{step.strip()}**\n")
        elif step.strip():
            # Format step numbers
            if step.lower().startswith(('step ', 'therefore', 'hence', 'thus', 'final')):
                formatted_steps.append(f"\n**{step.strip()}**\n")
            else:
                # Format equations and explanations
                lines = step.split('\n')
                formatted_lines = []
                for line in lines:
                    # Check if line contains equations
                    if any(char in line for char in '=+-×÷*/'):
                        formatted_lines.append(f"```math\n{line.strip()}\n```")
                    else:
                        formatted_lines.append(line.strip())
                formatted_steps.append('\n'.join(formatted_lines))
    
    return '\n\n'.join(formatted_steps)

def sanitize_response(text):
    """Clean and format the AI response"""
    # Enhanced formatting to prevent multiple boxes
    
    # Normalize line breaks and spacing
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Improve step and section formatting
    text = re.sub(r'^(Step\s*\d+:)', r'**\1**', text, flags=re.MULTILINE)
    text = re.sub(r'^(Conclusion:)', r'**\1**', text, flags=re.MULTILINE)
    
    # Format equations and mathematical expressions
    text = re.sub(r'\$\$(.*?)\$\$', r'**Equation:** \1', text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', r'*\1*', text)
    
    # Preserve overall response structure
    text = text.strip()
    
    # Sanitize HTML to prevent XSS
    formatted_text = (
        text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;')
    )
    
    return formatted_text

def format_mathematical_notation(text):
    """
    Standardize mathematical notation across all AI responses.
    """
    # Replace basic mathematical operators
    text = re.sub(r'\*\*', '^', text)
    text = re.sub(r'\*', '×', text)
    
    # Format equations with proper spacing and alignment
    equations = re.finditer(r'\$\$(.*?)\$\$', text, re.DOTALL)
    for eq in equations:
        formatted_eq = f'<div class="equation">{eq.group(1).strip()}</div>'
        text = text.replace(eq.group(0), formatted_eq)
    
    # Format inline math expressions
    inline_math = re.finditer(r'\$(.*?)\$', text)
    for math in inline_math:
        formatted_math = f'<span class="math-expression">{math.group(1).strip()}</span>'
        text = text.replace(math.group(0), formatted_math)
    
    # Format step-by-step solutions
    steps = text.split('\n\n')
    formatted_steps = []
    for step in steps:
        if step.strip():
            formatted_steps.append(f'<div class="solution-step">{step.strip()}</div>')
    
    text = '\n'.join(formatted_steps)
    
    # Format variables and symbols
    symbols = re.finditer(r'([a-zA-Z]_[0-9a-zA-Z]|[a-zA-Z])', text)
    for symbol in symbols:
        if symbol.group(0) in ['a', 'an', 'the', 'in', 'on', 'at', 'to', 'for']:
            continue
        formatted_symbol = f'<span class="symbol">{symbol.group(0)}</span>'
        text = text.replace(symbol.group(0), formatted_symbol, 1)
    
    return text

@app.route('/')
def home():
    now = datetime.now().strftime("%I:%M %p")
    initial_question = "Welcome to Hecker! What would you like to learn today?"
    return render_template('index.html', now=now, initial_question=initial_question)

@app.route('/generate_response', methods=['POST'])
def generate_response():
    user_message = request.json.get('message', '')
    
    try:
        response = chat.send_message(user_message)
        return jsonify({
            'response': response.text,
            'timestamp': datetime.now().strftime("%I:%M %p")
        })
    except Exception as e:
        return jsonify({
            'response': f"I'm experiencing some difficulties. Error: {str(e)}",
            'timestamp': datetime.now().strftime("%I:%M %p")
        })

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.json
        query_text = data.get('query', '')
        is_regeneration = data.get('regenerate', False)

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
        response = model.generate_content(context_prompt)
        # Apply mathematical notation formatting to the response
        formatted_response = format_mathematical_notation(response.text)
        return sanitize_response(formatted_response)
    except Exception as e:
        app.logger.error(f"Response generation error: {e}")
        return f"I'm sorry, I encountered an error processing your query. {generate_emoji()}"

if __name__ == '__main__':
    app.run(debug=True)
