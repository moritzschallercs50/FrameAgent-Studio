# FrameAgent Studio - Frontend

A modern, AI-powered brand video generation platform with a beautiful Flask-based web interface.

## Features

- **URL Analysis**: Enter your website URL to start the AI analysis
- **Brand Strategy**: View AI-generated brand core, positioning, and identity
- **Creative Concepts**: Browse 4 unique video ideas with editing capabilities
- **Script Generation**: Review and edit the 30-second video script
- **Storyboard**: Visualize each scene with generated frame descriptions
- **Video Player**: Watch the final generated video

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
FrameAgent-Studio/
├── app.py                      # Main Flask application
├── main.py                     # Backend agent logic (DO NOT MODIFY)
├── llm_library.py             # LLM functions (DO NOT MODIFY)
├── templates/                  # HTML templates
│   ├── base.html              # Base template with loading overlay
│   ├── index.html             # Page 1: URL input
│   ├── brand_strategy.html    # Page 2: Brand strategist
│   ├── creative_concepts.html # Page 3: Creative director
│   ├── script.html            # Page 4: Screenwriter
│   ├── storyboard.html        # Page 5: Storyboard
│   └── video.html             # Page 6: Video player
├── static/
│   ├── css/
│   │   └── styles.css         # Main stylesheet
│   └── js/
│       └── main.js            # JavaScript utilities
└── requirements.txt           # Python dependencies
```

## Page Flow

1. **Landing Page** (`/`)
   - Clean input field for website URL
   - Gradient background with modern hero section
   - Triggers research agent on submission

2. **Brand Strategy** (`/brand-strategy`)
   - Three card layout for Brand Core, Positioning, Identity
   - Auto-loads strategy analysis
   - Continue button to proceed

3. **Creative Concepts** (`/creative-concepts`)
   - 4-column grid of video ideas
   - Click any concept to expand and edit
   - Regenerate button with feedback modal
   - Select concept to proceed

4. **Script** (`/script`)
   - Full 30-second video script display
   - Scene-by-scene breakdown with timestamps
   - Edit mode for modifications
   - Continue to storyboard

5. **Storyboard** (`/storyboard`)
   - Grid layout of visual frames
   - Each card shows scene details and frame prompt
   - Placeholder for generated images
   - Generate video button

6. **Video Player** (`/video`)
   - Full-width video player
   - Download and share options
   - Create another video button

## API Endpoints

- `POST /api/analyze-url` - Analyze website URL
- `POST /api/brand-strategy` - Generate brand strategy
- `POST /api/creative-concepts` - Generate 4 video ideas
- `POST /api/regenerate-concepts` - Regenerate with feedback
- `POST /api/select-concept` - User selects a concept
- `POST /api/generate-script` - Generate video script
- `POST /api/update-script` - Save script edits
- `POST /api/generate-storyboard` - Generate storyboard frames
- `POST /api/generate-video` - Generate final video

## Design Features

- **Modern UI**: Clean, gradient backgrounds, rounded corners
- **Smooth Animations**: Hover effects, page transitions, loading states
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Loading States**: Beautiful loading overlays with custom messages
- **Modal Dialogs**: Concept editing and feedback modals
- **Card Layouts**: Consistent card-based design throughout
- **Color Palette**: Primary purple/blue gradients with neutral backgrounds

## Customization

### Colors
Edit CSS variables in `static/css/styles.css`:
```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --accent-color: #ec4899;
    /* ... */
}
```

### Loading Messages
Edit in HTML templates or pass to `showLoading()` function:
```javascript
showLoading('Custom Title', 'Custom message');
```

## Notes

- The backend (`main.py`, `llm_library.py`) should not be modified
- Flask session is used to maintain workflow state
- All agent interactions are mapped to frontend components
- Loading animations provide feedback during AI processing

