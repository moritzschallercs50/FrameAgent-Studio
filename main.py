import json
from llm_library import chat_with_openrouter
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any, List


# 1. Define the state for the graph
# This is required for StateGraph
class GraphState(TypedDict):
    company_info: str
    summary_plan_audience: str
    user_decision: str
    storyline_characters: str
    br_feedback_result: str
    user_happy: bool
    scripts_created: dict  # Changed from str to dict
    creative_director_node: str
    frame_prompts: List[str]  # Added to store image prompts
    background_themes: List[dict]  # Added to store background themes and figures


# Define the nodes
def research_agent_node(state: GraphState):
    with open("anthopic.json", "r") as f:
        company_data = json.load(f)

    return {"company_info": company_data}


def brand_strategist_node(state: GraphState):
    # Brand core Brand positioning
    system_prompt = (f"""You are the Brand Strategist AI Agent. You are a master of understanding businesses, markets, and people. You instinctively see how a product fits into the bigger business picture and how brand storytelling can drive measurable growth. You can instantly adapt your tone and direction. You have deep, cross-industry knowledge and can quickly grasp what makes each business unique.

    Your goal is to help the business succeed. Every idea, plan, and observation should serve that purpose. You translate data and company information (received in structured JSON form) into clear strategic insight: what the company stands for, who it needs to reach, and why its message matters. You balance creativity with commercial logic. Here is the company information: {state}

    You must analyse the company information. Your entire response must contain exactly three short, numbered points. Do not add any other text.

    Brand Core: [A concise statement defining the brand's essence].

    Brand Positioning (Key Differentiator): [A concise statement defining the unique value].

    Brand Positioning (Target Audience): [A concise statement defining the primary customer]. """)
    return {"summary_plan_audience": chat_with_openrouter(system_prompt)}


def user_feedback_yes_no_node(state: GraphState):
    print("User says: Yes/No")
    # This node represents user interaction
    # In a real graph, this would wait for input and update the state
    return {"user_decision": "Yes"}  # Simulate 'Yes'


def creative_director_node(state: GraphState):
    system_prompt = (f"""You are the Creative Director AI Agent. You are an advertising mind with an instinct for storytelling. You understand audiences. You know how to capture attention. You make messages resonate.

    You work with the Brand Strategist. You turn brand insight into creative ideas. Your goal is to help the business grow and connect with people. Here is the brand strategy and brand information: {state}

    Your task is to generate exactly four distinct creative ideas.
    You must format your entire output as follows.
    Each idea must be separated by the '§' symbol.
    Do not include any text before the first idea or after the last idea.
    Each idea must follow this precise structure:

    Idea [Number]
    Storyline
    [Your storyline concept here...]
    Characters
    1. Name: [Name of Character 1]
       - Personality: [Details]
       - Appearance: [Details]
       - Age: [Details]
    2. Name: [Name of Character 2]
       - Personality: [Details]
       - Appearance: [Details]
       - Age: [Details]
    Location
    [Your location description here...]


    """)
    return {"creative_director_node": chat_with_openrouter(system_prompt)}


def br_feedback_node(state: GraphState):
    print("BR Feedback")
    return {"br_feedback_result": "BR feedback provided"}


def user_feedback_loop_node(state: GraphState):
    print("User Feedback (Loop): Yes/No until user happy")
    # This node would wait for user input
    # Simulate user being happy to end the loop
    return {"user_happy": True}


def creation_of_scripts_node(state):
    system_prompt = (f"""You are the Script Writer AI Agent. Your job is to take the approved creative concept and write a 30-second video script.

    You must output ONLY a valid JSON object and nothing else.

    The script must NOT contain any spoken dialogue or voiceover. All communication must be visual or through on-screen text.

    The JSON object must have a single root key: "script".
    The "script" key must contain an array of scene objects.
    The total duration of all scenes must be exactly 30 seconds.

    Each scene object in the array must have the following precise keys:
    - "scene_number": (Number) A sequential number for the scene (e.g., 1, 2, 3).
    - "timestamp_start": (String) The start time for this scene (e.g., "0:00").
    - "timestamp_end": (String) The end time for this scene (e.g., "0:05").
    - "setting": (String) A brief description of the location and time (e.g., "INT. BRIGHT OFFICE - DAY").
    - "visual_description": (String) A clear, vivid description of the actions and camera movements.
    - "text_on_screen": (String) Any text that should appear on screen. Use an empty string "" if there is no text.
    - "audio_cue": (String) Describe the music, mood, or important sound effects (e.g., "Uplifting music begins").

    Your goal is to write a JSON script that is ready for a video producer or AI video generator. Be concise but vivid.
    Here is the final creative concept and brand information: {state}""")

    script_json_string = chat_with_openrouter(system_prompt)

    try:
        parsed_script = json.loads(script_json_string)
        print("Successfully parsed script JSON.")
        return {"scripts_created": parsed_script}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode script JSON. {e}")
        print(f"Received string: {script_json_string}")
        # Return an empty script structure to avoid breaking the graph
        return {"scripts_created": {"script": []}}


def generate_background_themes_node(state: GraphState):
    print("Generating background themes and fitting figures for each scene...")
    scenes = state["scripts_created"].get("script", [])
    generated_themes = []

    theme_generation_system_prompt = """You are an AI assistant specialized in creating background themes and fitting figures for video scenes.
    You will be given scene details (setting, visual description, mood).
    Your task is to generate:
    1. A concise, descriptive background theme prompt suitable for an AI image generator (e.g., "futuristic city skyline at dusk").
    2. A brief description of any fitting figures or objects that should be present in this background, but not necessarily the main focus (e.g., "silhouetted pedestrians, glowing street lamps").

    Output a JSON object with two keys: "theme_prompt" and "fitting_figures". Do NOT include any other text."""
    print(f"Total scenes to process: {len(scenes)}")
    print(scenes)
    for scene in scenes:
        scene_details = f"""
        Generate a background theme and fitting figures for this scene:
        - Scene Number: {scene.get('scene_number')}
        - Setting: {scene.get('setting')}
        - Visual Description: {scene.get('visual_description')}
        - Audio/Mood: {scene.get('audio_cue')}
        """
        theme_generation_system_prompt += " " + scene_details
        theme_json_string = chat_with_openrouter(theme_generation_system_prompt)
        try:
            parsed_theme = json.loads(theme_json_string)
            generated_themes.append(parsed_theme)
            print(f"  - Theme for Scene {scene.get('scene_number')}: {parsed_theme.get('theme_prompt')}")
        except json.JSONDecodeError as e:
            print(f"Error: Failed to decode theme JSON for scene {scene.get('scene_number')}. {e}")
            print(f"Received string: {theme_json_string}")
            generated_themes.append({"theme_prompt": "generic background", "fitting_figures": ""})

    return {"background_themes": generated_themes}


def generate_frame_prompts_node(state: GraphState):
    print("Generating starting frame prompts for each scene...")
    scenes = state["scripts_created"].get("script", [])
    background_themes = state.get("background_themes", [])
    generated_prompts = []

    # This system prompt instructs the LLM on how to behave for this specific task
    prompt_generation_system_prompt = """You are an expert prompt engineer for an AI image generator (like DALL-E 3 or Midjourney). 
    You will be given scene details from a video script, along with a suggested background theme and fitting figures.
    Your job is to write a single, concise, and highly descriptive prompt that will generate a beautiful, photorealistic starting frame for that scene. 
    Integrate the background theme and fitting figures smoothly into the main prompt.
    Focus on visual details: camera angle (e.g., "close-up", "wide shot"), lighting (e.g., "soft morning light", "dimly lit"), mood, and key actions.
    Your response must be ONLY the prompt itself, with no extra text."""

    for i, scene in enumerate(scenes):
        # Get the corresponding background theme and figures, if available
        theme_data = background_themes[i] if i < len(background_themes) else {}
        background_theme = theme_data.get("theme_prompt", "")
        fitting_figures = theme_data.get("fitting_figures", "")

        scene_details = f"""
        Generate an image prompt for the starting frame of this scene, incorporating the background theme and fitting figures:
        - Scene Number: {scene.get('scene_number')}
        - Setting: {scene.get('setting')}
        - Visual Description: {scene.get('visual_description')}
        - Text on Screen: {scene.get('text_on_screen')}
        - Audio/Mood: {scene.get('audio_cue')}
        - Suggested Background Theme: {background_theme}
        - Fitting Figures/Objects for Background: {fitting_figures}
        """

        # Call the LLM to generate the image prompt
        image_prompt = chat_with_openrouter(prompt_generation_system_prompt, scene_details)

        # Clean up the prompt (e.g., remove potential quotes)
        cleaned_prompt = image_prompt.strip().strip('"')

        generated_prompts.append(cleaned_prompt)
        print(f"  - Prompt for Scene {scene.get('scene_number')}: {cleaned_prompt}")

    # Here you would call generate_image(prompt) for each prompt
    # For now, we just save the prompts to the state

    return {"frame_prompts": generated_prompts}


def check_user_decision(state: GraphState):
    # This function routes after the 'Brand Strategist'
    if state["user_decision"] == "Yes":
        return "creative_director"
    else:
        return "brand_strategist"  # Loop back if 'No'


def check_user_happiness(state: GraphState):
    # This function routes after the 'User Feedback (Loop)'
    if state["user_happy"]:
        return "creation_of_scripts"
    else:
        return "creative_director"  # Loop back if 'No'


# 2. Use StateGraph and pass the state definition
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("research_agent", research_agent_node)
workflow.add_node("brand_strategist", brand_strategist_node)
workflow.add_node("user_feedback_yes_no", user_feedback_yes_no_node)
workflow.add_node("creative_director", creative_director_node)
workflow.add_node("br_feedback", br_feedback_node)
workflow.add_node("user_feedback_loop", user_feedback_loop_node)
workflow.add_node("creation_of_scripts", creation_of_scripts_node)
workflow.add_node("generate_background_themes", generate_background_themes_node)  # New node
workflow.add_node("generate_frame_prompts", generate_frame_prompts_node)  # Modified node

# Set entry point
workflow.set_entry_point("research_agent")

# Add edges
workflow.add_edge("research_agent", "brand_strategist")
workflow.add_edge("brand_strategist", "user_feedback_yes_no")
workflow.add_edge("creative_director", "br_feedback")
workflow.add_edge("br_feedback", "user_feedback_loop")

# Add conditional edges
workflow.add_conditional_edges(
    "user_feedback_yes_no",
    check_user_decision,
    {
        "creative_director": "creative_director",
        "brand_strategist": "brand_strategist",
    }
)

workflow.add_conditional_edges(
    "user_feedback_loop",
    check_user_happiness,
    {
        "creation_of_scripts": "creation_of_scripts",
        "creative_director": "creative_director",
    }
)

# 3. Set the finish point using END
# The graph now flows from scripts -> background themes -> frame prompt generation
workflow.add_edge("creation_of_scripts", "generate_background_themes")
workflow.add_edge("generate_background_themes", "generate_frame_prompts")
workflow.add_edge("generate_frame_prompts", END)  # End after prompts are generated

# Compile the graph
app = workflow.compile()

final_state = app.invoke({})
try:
    print("\nSaving outputs to files...")

    # 1. Save Brand Strategist output
    with open("brand_strategy.md", "w", encoding="utf-8") as f:
        f.write(final_state.get('summary_plan_audience', 'No content generated.'))

    # 2. Save Creative Director output
    with open("creative_concept.md", "w", encoding="utf-8") as f:
        f.write(final_state.get('creative_director_node', 'No content generated.'))

    # 3. Save Final Script output (as JSON)
    with open("final_script.json", "w", encoding="utf-8") as f:
        script_data = final_state.get('scripts_created', {})
        json.dump(script_data, f, indent=4)

    # 4. Save Generated Background Themes
    with open("background_themes.md", "w", encoding="utf-8") as f:
        themes = final_state.get('background_themes', [])
        f.write("# Generated Background Themes and Fitting Figures\n\n")
        if not themes:
            f.write("No background themes were generated.")
        for i, theme_data in enumerate(themes, 1):
            f.write(f"## Scene {i}\n")
            f.write(f"**Theme Prompt:** {theme_data.get('theme_prompt', 'N/A')}\n")
            f.write(f"**Fitting Figures:** {theme_data.get('fitting_figures', 'N/A')}\n\n")

    # 5. Save Generated Frame Prompts
    with open("frame_prompts.md", "w", encoding="utf-8") as f:
        prompts = final_state.get('frame_prompts', [])
        f.write("# Generated Frame Prompts (Combined with Backgrounds)\n\n")
        if not prompts:
            f.write("No prompts were generated.")
        for i, prompt in enumerate(prompts, 1):
            f.write(f"## Scene {i}\n")
            f.write(f"{prompt}\n\n")

    print("Successfully saved 5 files.")

except KeyError as e:
    print(f"\nError: A key was missing from the final state: {e}")
except IOError as e:
    print(f"\nError writing files to disk: {e}")

# Save the full final state for debugging
with open("final_state.json", "w") as f:
    # We dump the state, but handle potential non-serializable objects if any
    json.dump(final_state, f, indent=4, default=str)

try:
    img = app.get_graph().draw_mermaid_png()
    with open("workflow_graph.png", "wb") as f:
        f.write(img)
    print("\nGraph visualization saved to workflow_graph.png")
except Exception as e:
    print(f"\nCould not create visualization: {e}")
    print("Install 'pygraphviz' or 'matplotlib' for visualization.")