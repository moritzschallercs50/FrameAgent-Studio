from flask import Flask, render_template, request, jsonify, session
import json
import os
from main import (
    research_agent_node,
    brand_strategist_node,
    creative_director_node,
    creation_of_scripts_node,
    generate_global_themes_node,
    generate_frame_prompts_node,
    GraphState
)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Store the workflow state
workflow_state = {}


@app.route('/')
def index():
    """Landing page with URL input"""
    return render_template('index.html')


@app.route('/api/analyze-url', methods=['POST'])
def analyze_url():
    """Process the URL and start the workflow"""
    data = request.json
    url = data.get('url')
    
    # Initialize state
    state = {
        'company_info': '',
        'summary_plan_audience': '',
        'user_decision': '',
        'storyline_characters': '',
        'br_feedback_result': '',
        'user_happy': False,
        'scripts_created': {},
        'creative_director_node': '',
        'frame_prompts': [],
        'global_themes_and_figures': {}
    }
    
    # Run research agent
    result = research_agent_node(state)
    state.update(result)
    
    # Store in session
    session['workflow_state'] = state
    
    return jsonify({'status': 'success', 'company_info': state['company_info']})


@app.route('/api/brand-strategy', methods=['POST'])
def generate_brand_strategy():
    """Generate brand strategy"""
    state = session.get('workflow_state', {})
    
    # Run brand strategist
    result = brand_strategist_node(state)
    state.update(result)
    
    # Parse the brand strategy output
    strategy_text = state['summary_plan_audience']
    
    session['workflow_state'] = state
    
    return jsonify({
        'status': 'success',
        'strategy': strategy_text,
        'raw_output': strategy_text
    })


@app.route('/api/creative-concepts', methods=['POST'])
def generate_creative_concepts():
    """Generate 4 creative video ideas"""
    state = session.get('workflow_state', {})
    
    # Run creative director
    result = creative_director_node(state)
    state.update(result)
    
    # Parse the creative concepts (separated by §)
    concepts_text = state['creative_director_node']
    concepts = concepts_text.split('§')
    
    # Clean and structure the concepts
    structured_concepts = []
    for i, concept in enumerate(concepts):
        if concept.strip():
            structured_concepts.append({
                'id': i + 1,
                'content': concept.strip()
            })
    
    session['workflow_state'] = state
    
    return jsonify({
        'status': 'success',
        'concepts': structured_concepts
    })


@app.route('/api/regenerate-concepts', methods=['POST'])
def regenerate_concepts():
    """Regenerate creative concepts based on user feedback"""
    data = request.json
    feedback = data.get('feedback', '')
    
    state = session.get('workflow_state', {})
    
    # Add feedback to state
    state['br_feedback_result'] = feedback
    
    # Re-run creative director with feedback
    result = creative_director_node(state)
    state.update(result)
    
    # Parse the creative concepts
    concepts_text = state['creative_director_node']
    concepts = concepts_text.split('§')
    
    structured_concepts = []
    for i, concept in enumerate(concepts):
        if concept.strip():
            structured_concepts.append({
                'id': i + 1,
                'content': concept.strip()
            })
    
    session['workflow_state'] = state
    
    return jsonify({
        'status': 'success',
        'concepts': structured_concepts
    })


@app.route('/api/select-concept', methods=['POST'])
def select_concept():
    """User selects a concept"""
    data = request.json
    concept_id = data.get('concept_id')
    
    state = session.get('workflow_state', {})
    state['user_happy'] = True
    
    session['workflow_state'] = state
    
    return jsonify({'status': 'success'})


@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    """Generate the video script"""
    state = session.get('workflow_state', {})
    
    # Run script creation
    result = creation_of_scripts_node(state)
    state.update(result)
    
    session['workflow_state'] = state
    
    return jsonify({
        'status': 'success',
        'script': state['scripts_created']
    })


@app.route('/api/update-script', methods=['POST'])
def update_script():
    """Update the script with user edits"""
    data = request.json
    updated_script = data.get('script')
    
    state = session.get('workflow_state', {})
    state['scripts_created'] = updated_script
    
    session['workflow_state'] = state
    
    return jsonify({'status': 'success'})


@app.route('/api/generate-storyboard', methods=['POST'])
def generate_storyboard():
    """Generate storyboard frames"""
    state = session.get('workflow_state', {})
    
    # Run global themes generation
    result = generate_global_themes_node(state)
    state.update(result)
    
    # Run frame prompts generation
    result = generate_frame_prompts_node(state)
    state.update(result)
    
    session['workflow_state'] = state
    
    # Combine script scenes with frame prompts
    scenes = state['scripts_created'].get('script', [])
    prompts = state['frame_prompts']
    
    storyboard = []
    for i, scene in enumerate(scenes):
        storyboard.append({
            'scene_number': scene.get('scene_number'),
            'timestamp': f"{scene.get('timestamp_start')} - {scene.get('timestamp_end')}",
            'setting': scene.get('setting'),
            'visual_description': scene.get('visual_description'),
            'text_on_screen': scene.get('text_on_screen'),
            'audio_cue': scene.get('audio_cue'),
            'image_prompt': prompts[i] if i < len(prompts) else ''
        })
    
    return jsonify({
        'status': 'success',
        'storyboard': storyboard
    })


@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Generate the final video (placeholder for now)"""
    # This would integrate with a video generation service
    return jsonify({
        'status': 'success',
        'video_url': '/static/sample-video.mp4'  # Placeholder
    })


@app.route('/brand-strategy')
def brand_strategy_page():
    """Brand strategist page"""
    return render_template('brand_strategy.html')


@app.route('/creative-concepts')
def creative_concepts_page():
    """Creative director page"""
    return render_template('creative_concepts.html')


@app.route('/script')
def script_page():
    """Screenwriter page"""
    return render_template('script.html')


@app.route('/storyboard')
def storyboard_page():
    """Storyboard page"""
    return render_template('storyboard.html')


@app.route('/video')
def video_page():
    """Final video player page"""
    return render_template('video.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)

