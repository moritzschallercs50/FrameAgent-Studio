from flask import Flask, render_template, request, jsonify, session
import json
import os
import re
import requests
from urllib.parse import urlparse
from uuid import uuid4
from llm_library import generate_image_with_style
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


def _normalize_domain(url: str) -> str:
    try:
        parsed = urlparse(url if re.match(r'^https?://', url) else f'https://{url}')
        host = parsed.netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return ''


def _get_brandfetch_api_key():
    key = os.getenv('BRANDFETCH_API_KEY')
    if key:
        return key
    # Try local files
    for fname in ['.brandfetch_key', 'brandfetch_api_key.txt', 'brandfetch.key']:
        if os.path.exists(fname):
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception:
                pass
    # Fallback: parse research test.py Authorization header if present
    try:
        if os.path.exists('research test.py'):
            with open('research test.py', 'r', encoding='utf-8') as f:
                text = f.read()
            m = re.search(r'"Authorization"\s*:\s*"Bearer\s+([^"]+)"', text)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def _fetch_brand_from_brandfetch(domain: str):
    api_key = _get_brandfetch_api_key()
    if not api_key or not domain:
        return None
    try:
        resp = requests.get(
            f'https://api.brandfetch.io/v2/brands/{domain}',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=12,
        )
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return None


def _fetch_brand_via_transaction(url: str, country_code: str = None):
    api_key = _get_brandfetch_api_key()
    if not api_key or not url:
        return None
    payload = {
        "transactionLabel": url,
    }
    if country_code:
        payload["countryCode"] = country_code
    try:
        resp = requests.post(
            'https://api.brandfetch.io/v2/brands/transaction',
            json=payload,
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            timeout=15,
        )
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return None


def _scrape_basic_brand_info(url: str, domain: str):
    info = {
        'id': domain,
        'name': domain.split('.')[0].capitalize() if domain else 'Brand',
        'domain': domain,
        'description': '',
        'longDescription': '',
        'pageTitle': '',
        'metaDescription': '',
        'links': [],
        'logos': [],
        'colors': [],
        'fonts': [],
        'images': [],
        'qualityScore': 0.0,
        'company': {},
        'isNsfw': False,
        'urn': f'urn:brand:{domain}'
    }
    if not url:
        return info
    try:
        target = url if re.match(r'^https?://', url) else f'https://{url}'
        resp = requests.get(target, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.ok:
            return info
        html = resp.text or ''
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        meta_match = re.search(r'<meta[^>]*name=["\"]description["\"][^>]*content=["\"]([^"\"]+)["\"][^>]*>', html, re.IGNORECASE)
        title = (title_match.group(1).strip() if title_match else '')
        description = (meta_match.group(1).strip() if meta_match else '')
        info['pageTitle'] = title
        info['metaDescription'] = description
        if title:
            info['name'] = title.split('|')[0].split('—')[0].strip()
        if description:
            info['description'] = description
            info['longDescription'] = description
        return info
    except Exception:
        return info


def _load_local_brand(domain: str):
    # Try domain-based JSON file for quick demos; fallback to anthopic.json
    try:
        if domain and os.path.exists(f'{domain}.json'):
            with open(f'{domain}.json', 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # Some demo files may be Python dicts -> try eval safely
                    import ast
                    f.seek(0)
                    return ast.literal_eval(f.read())
    except Exception:
        pass
    try:
        with open('anthopic.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


@app.route('/')
def index():
    """Landing page with URL input"""
    return render_template('index.html')


@app.route('/api/analyze-url', methods=['POST'])
def analyze_url():
    """Process the URL and start the workflow"""
    data = request.json
    url = (data or {}).get('url') or ''
    domain = _normalize_domain(url)

    # Initialize state
    state = {
        'submitted_url': url,
        'domain': domain,
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

    # Prefer Brandfetch API if available; else scrape; else local fallback
    # 1) Try Brandfetch transaction (more robust for full URLs)
    company_info = _fetch_brand_via_transaction(url, os.getenv('BRANDFETCH_COUNTRY') or None)
    # 2) Fallback to simple Brandfetch by domain
    if not company_info:
        company_info = _fetch_brand_from_brandfetch(domain)
    if not company_info:
        company_info = _scrape_basic_brand_info(url, domain)
    if not company_info:
        company_info = _load_local_brand(domain)

    # Always try to enrich with page meta
    try:
        meta = _scrape_basic_brand_info(url, domain)
        if isinstance(company_info, dict) and isinstance(meta, dict):
            if not company_info.get('pageTitle') and meta.get('pageTitle'):
                company_info['pageTitle'] = meta.get('pageTitle')
            if not company_info.get('metaDescription') and meta.get('metaDescription'):
                company_info['metaDescription'] = meta.get('metaDescription')
    except Exception:
        pass

    state['company_info'] = company_info

    # Store in session
    if 'session_id' not in session:
        session['session_id'] = uuid4().hex
    session['workflow_state'] = state

    return jsonify({'status': 'success', 'company_info': state['company_info'], 'domain': domain})


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

    # Persist concepts for later selection
    state['structured_concepts'] = structured_concepts
    # Clear any previous selection upon regeneration
    state['selected_concept_id'] = None
    state['selected_concept'] = None

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

    # Persist and clear selection on regeneration
    state['structured_concepts'] = structured_concepts
    state['selected_concept_id'] = None
    state['selected_concept'] = None

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
    content = data.get('content')

    state = session.get('workflow_state', {})
    # Save selection
    state['selected_concept_id'] = concept_id
    if content:
        state['selected_concept'] = content
    else:
        for c in state.get('structured_concepts', []):
            if c.get('id') == concept_id:
                state['selected_concept'] = c.get('content')
                break
    # Mark user approval for next step
    state['user_happy'] = True

    session['workflow_state'] = state

    return jsonify({'status': 'success'})


@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    """Generate the video script"""
    state = session.get('workflow_state', {})

    # Run script creation (uses selected_concept from state)
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
    # Prepare output directory for generated images
    session_id = session.get('session_id') or uuid4().hex
    session['session_id'] = session_id
    base_dir = os.path.join('static', 'generated', 'storyboards', session_id)
    os.makedirs(base_dir, exist_ok=True)

    for i, scene in enumerate(scenes):
        image_url = ''
        prompt_text = prompts[i] if i < len(prompts) else ''
        # Try to generate an image and save it
        try:
            if prompt_text:
                img_bytes = generate_image_with_style(prompt_text, style="Photorealistic")
                if img_bytes:
                    # Build deterministic, readable filename using scene number and timestamps
                    ts_start = str(scene.get('timestamp_start', '') or '').replace(':', '-').replace(' ', '')
                    ts_end = str(scene.get('timestamp_end', '') or '').replace(':', '-').replace(' ', '')
                    parts = ["scene", str(scene.get('scene_number') or i + 1)]
                    if ts_start or ts_end:
                        parts += [ts_start or 'start', ts_end or 'end']
                    filename = "_".join(parts) + ".png"
                    filepath = os.path.join(base_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(img_bytes)
                    image_url = f"/static/generated/storyboards/{session_id}/{filename}"
        except Exception:
            image_url = ''

        storyboard.append({
            'scene_number': scene.get('scene_number'),
            'timestamp': f"{scene.get('timestamp_start')} - {scene.get('timestamp_end')}",
            'setting': scene.get('setting'),
            'visual_description': scene.get('visual_description'),
            'text_on_screen': scene.get('text_on_screen'),
            'audio_cue': scene.get('audio_cue'),
            'image_prompt': prompt_text,
            'image_url': image_url
        })

    return jsonify({
        'status': 'success',
        'storyboard': storyboard
    })


@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Generate the final video (placeholder for now)"""
    # Hardcoded demo: pick first video in static/demo/final_video
    demo_dir = os.path.join('static', 'demo', 'final_video')
    video_url = '/static/sample-video.mp4'
    try:
        if os.path.isdir(demo_dir):
            exts = {'.mp4', '.webm', '.mov', '.m4v'}
            entries = [n for n in sorted(os.listdir(demo_dir)) if os.path.isfile(os.path.join(demo_dir, n))]
            # Prefer known video extensions first
            for name in entries:
                _, ext = os.path.splitext(name)
                if ext.lower() in exts:
                    video_url = f"/static/demo/final_video/{name}"
                    break
            else:
                # If no known extensions matched, just take the first file present
                if entries:
                    video_url = f"/static/demo/final_video/{entries[0]}"
    except Exception:
        pass
    return jsonify({'status': 'success', 'video_url': video_url})


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

