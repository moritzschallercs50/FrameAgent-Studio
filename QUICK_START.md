# 🎬 FrameAgent Studio - Quick Start Guide

## 🚀 Getting Started (3 Easy Steps)

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Start the Server
```bash
python app.py
```
Or use the convenience script:
```bash
./start.sh
```

### 3️⃣ Open Your Browser
Navigate to: **http://localhost:5000**

---

## 📱 User Flow

### Page 1: Landing Page 🏠
- **URL**: `/`
- **Purpose**: Enter your website URL
- **Design**: Beautiful gradient background with centered input field
- **Action**: Click "Analyze" to start

### Page 2: Brand Strategy 📊
- **URL**: `/brand-strategy`
- **Purpose**: View AI-generated brand analysis
- **Sections**:
  - Brand Core (Mission, Values, Product)
  - Brand Positioning (Target Audience, Differentiators, Promise)
  - Brand Identity (Name, Logo, Typography, Colors, Tone, Tagline)
- **Layout**: 3-column card grid
- **Action**: Click "Generate Video Ideas"

### Page 3: Creative Concepts 💡
- **URL**: `/creative-concepts`
- **Purpose**: Browse and select video concepts
- **Features**:
  - 4 video ideas in card layout
  - Click any card to expand and edit
  - Regenerate button with feedback modal
  - Editable storyline, characters, and location
- **Action**: Select a concept and click "Generate Script"

### Page 4: Script 📝
- **URL**: `/script`
- **Purpose**: Review and edit video script
- **Features**:
  - Scene-by-scene breakdown
  - Timestamps for each scene
  - Edit mode (click pencil icon)
  - Visual description, text on screen, audio cues
- **Action**: Click "Generate Storyboard"

### Page 5: Storyboard 🎨
- **URL**: `/storyboard`
- **Purpose**: Visualize each scene
- **Layout**: Grid of storyboard cards
- **Each Card Shows**:
  - Frame placeholder (16:9 aspect ratio)
  - Timestamp
  - Scene number
  - Setting
  - Visual description
  - Text on screen
- **Action**: Click "Generate Final Video"

### Page 6: Video Player 🎥
- **URL**: `/video`
- **Purpose**: Watch the final video
- **Features**:
  - Full video player with controls
  - Download button
  - Share button
  - Create another video button

---

## 🎨 Design Features

✨ **Modern UI Elements**:
- Rounded cards with soft shadows
- Smooth hover animations
- Gradient backgrounds on landing page
- Loading overlays with custom messages
- Modal dialogs for editing
- Responsive design (works on mobile, tablet, desktop)

🎨 **Color Palette**:
- Primary: Purple/Blue gradient (#6366f1 → #8b5cf6)
- Accent: Pink (#ec4899)
- Background: Light gray (#fafafa)
- Surface: White (#ffffff)
- Text: Dark gray (#1f2937)

---

## 🔧 Technical Details

### Backend Routes
All routes map to backend functions in `main.py`:
- Research Agent → URL analysis
- Brand Strategist → Brand strategy generation
- Creative Director → Video concepts
- Screenwriter → Script generation
- Storyboard Artist → Frame prompts

### State Management
- Flask sessions store workflow state
- Session lifetime: 30 minutes
- State persists across page navigation

### File Structure
```
FrameAgent-Studio/
├── app.py                  # Flask application ✅
├── templates/              # HTML templates ✅
│   ├── base.html
│   ├── index.html
│   ├── brand_strategy.html
│   ├── creative_concepts.html
│   ├── script.html
│   ├── storyboard.html
│   └── video.html
├── static/
│   ├── css/
│   │   └── styles.css     # Complete styling ✅
│   └── js/
│       └── main.js        # Utilities ✅
├── main.py                # Backend (unchanged)
├── llm_library.py         # LLM functions (unchanged)
└── requirements.txt       # Dependencies ✅
```

---

## 🎯 Key Features Implemented

✅ **Page Navigation**: Smooth transitions between pages
✅ **Loading States**: Beautiful loading overlays with agent status
✅ **Modals**: Concept editing and feedback dialogs
✅ **Edit Functionality**: Script and concept editing
✅ **Responsive Design**: Works on all screen sizes
✅ **Modern Styling**: Cards, shadows, gradients, animations
✅ **API Integration**: All backend functions mapped to frontend
✅ **Session Management**: Workflow state persistence

---

## 🎬 Loading Messages

Each transition shows relevant loading messages:
- "Analyzing your brand..." (URL → Brand Strategy)
- "Brand Strategist at work..." (Generating strategy)
- "Creative Director thinking..." (Generating concepts)
- "Creative Director revising..." (Regenerating with feedback)
- "Screenwriter at work..." (Generating script)
- "Storyboard artist at work..." (Generating storyboard)
- "Video Generator at work..." (Generating video)

---

## 📝 Notes

- Backend files (`main.py`, `llm_library.py`) remain unchanged
- All agent outputs are properly mapped to frontend fields
- Loading animations provide visual feedback during AI processing
- Session state maintains workflow data across pages
- Modals allow in-place editing without page reload

---

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change port in app.py, line: app.run(debug=True, port=5000)
```

**Missing dependencies?**
```bash
pip install --upgrade -r requirements.txt
```

**Session errors?**
```bash
# Clear Flask session files
rm -rf flask_session/
```

---

## 🎉 You're All Set!

Run `python app.py` and start creating amazing AI-generated brand videos! 🚀

