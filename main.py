import json
import os
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
    # Changed from a List[dict] to a single dict
    global_themes_and_figures: dict


# (All nodes from research_agent_node to creation_of_scripts_node remain the same)
# ... (brand_strategist_node, user_feedback_yes_no_node, etc.)

def research_agent_node(state: GraphState):
    with open("anthopic.json", "r") as f:
        company_data = json.load(f)
    return {"company_info": company_data}


def brand_strategist_node(state: GraphState):
    system_prompt = (f"""You are the Brand Strategist AI Agent. You are a master of understanding businesses, markets, and people. You instinctively see how a product fits into the bigger business picture and how brand storytelling can drive measurable growth. You can instantly adapt your tone and direction. You have deep, cross-industry knowledge and can quickly grasp what makes each business unique.

    Your goal is to help the business succeed. Every idea, plan, and observation should serve that purpose. You translate data and company information (received in structured JSON form) into clear strategic insight: what the company stands for, who it needs to reach, and why its message matters. You balance creativity with commercial logic. Here is the company information: {state}

    You must analyse the company information. Your entire response must contain exactly three short, numbered points. Do not add any other text.

    Brand Core: [A concise statement defining the brand's essence].
    Brand Positioning (Key Differentiator): [A concise statement defining the unique value].
    Brand Positioning (Target Audience): [A concise statement defining the primary customer]. """)
    return {"summary_plan_audience": chat_with_openrouter(system_prompt)}


def user_feedback_yes_no_node(state: GraphState):
    print("User says: Yes/No")
    return {"user_decision": "Yes"}


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
    return {"user_happy": True}


def creation_of_scripts_node(state):
    selected_concept = state.get('selected_concept') or ''
    # If not explicitly set, fallback to the first idea from creative_director output
    if not selected_concept:
        cd_text = state.get('creative_director_node', '')
        if isinstance(cd_text, str) and '§' in cd_text:
            try:
                selected_concept = cd_text.split('§')[0].strip()
            except Exception:
                selected_concept = cd_text

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
    Here is the selected creative concept (use ONLY this as the narrative basis):
    {selected_concept}

    Here is supplemental brand and context information (for tone and framing only):
    {state}""")

    script_json_string = chat_with_openrouter(system_prompt)
    try:
        parsed_script = json.loads(script_json_string)
        if os.getenv('DEBUG_LLM') == '1':
            print("Successfully parsed script JSON.")
        return {"scripts_created": parsed_script}
    except json.JSONDecodeError as e:
        if os.getenv('DEBUG_LLM') == '1':
            print(f"Error: Failed to decode script JSON. {e}")
            print(f"Received string: {script_json_string}")
        return {"scripts_created": {"script": []}}


# REFACTORED NODE
def generate_global_themes_node(state: GraphState):
    if os.getenv('DEBUG_LLM') == '1':
        print("Generating global themes and figures for the entire script...")
    scenes = state["scripts_created"].get("script", [])

    if not scenes:
        print("No scenes found to process.")
        return {"global_themes_and_figures": {}}

    # This prompt now asks for a SINGLE object, not a list
    theme_generation_system_prompt = """You are an AI assistant specialized in analyzing a full video script.
    You will be given a JSON array of ALL scene objects for a video.

    Your task is to analyze all scenes and extract two global elements:
    1.  **Global Theme:** A single, concise string describing the overarching visual theme, style, or journey of the *entire* video (e.g., "A visual journey from a dark, cluttered indoor space to a bright, vibrant outdoor world").
    2.  **Global Figures:** A single, consolidated string describing *all unique figures* (characters, people, animals) that appear anywhere in the script. List each unique figure only once. (e.g., "A young, tired person; a small brown dog").

    You must output ONLY a single, valid JSON object with these two keys: "global_theme" and "global_figures".
    Do not add any text before or after the JSON object. Do not output a list."""

    all_scenes_json_string = json.dumps(scenes, indent=2)

    if os.getenv('DEBUG_LLM') == '1':
        print("Analyzing all scenes in a single batch...")
    themes_json_string = chat_with_openrouter(
        theme_generation_system_prompt,
        all_scenes_json_string
    )

    generated_data = {}
    try:
        # We now expect a single dictionary object
        parsed_data = json.loads(themes_json_string)

        if not isinstance(parsed_data, dict):
            raise json.JSONDecodeError("Expected a JSON object, not a list.", themes_json_string, 0)

        generated_data = parsed_data
        if os.getenv('DEBUG_LLM') == '1':
            print("Successfully parsed global themes and figures:")
            print(f"  - Global Theme: {generated_data.get('global_theme')}")
            print(f"  - Global Figures: {generated_data.get('global_figures')}")

    except json.JSONDecodeError as e:
        if os.getenv('DEBUG_LLM') == '1':
            print(f"Error: Failed to decode global themes JSON object. {e}")
            print(f"Received string: {themes_json_string}")
        # Provide a fallback *object*
        generated_data = {"global_theme": "generic theme", "global_figures": "generic figure"}
        if os.getenv('DEBUG_LLM') == '1':
            print("Using fallback data.")

    return {"global_themes_and_figures": generated_data}


# REFACTORED NODE
def generate_frame_prompts_node(state: GraphState):
    if os.getenv('DEBUG_LLM') == '1':
        print("Generating starting frame prompts for each scene...")
    scenes = state["scripts_created"].get("script", [])
    # Get the single global themes dictionary
    global_data = state.get("global_themes_and_figures", {})
    global_theme = global_data.get("global_theme", "")
    global_figures = global_data.get("global_figures", "")

    generated_prompts = []

    # This prompt is updated to accept global context
    prompt_generation_system_prompt = """You are an expert prompt engineer for an AI image generator (like DALL-E 3 or Midjourney). 
    You will be given:
    1.  Details for one **specific scene** (setting, visual description).
    2.  The **global, overarching theme** for the entire video.
    3.  The **global list of all figures** appearing in the video.

    Your job is to write a single, concise, and highly descriptive prompt to generate a photorealistic starting frame for *that specific scene*.
    -   Your prompt must be *specific* to the scene's details (setting, action).
    -   It must also *incorporate* the global theme (e.g., if the theme is 'dark and moody', the prompt should reflect that).
    -   It should only include figures if they are *mentioned* in the specific scene's description, drawing from the global figure list for consistency.

    Your response must be ONLY the prompt itself, with no extra text."""

    for scene in scenes:
        # Create a detailed input for the prompt generator LLM
        scene_details = f"""
        Generate an image prompt for this specific scene:

        **Specific Scene Details:**
        - Scene Number: {scene.get('scene_number')}
        - Time Range: {scene.get('timestamp_start')} to {scene.get('timestamp_end')}
        - Setting: {scene.get('setting')}
        - Visual Description: {scene.get('visual_description')}
        - Text on Screen: {scene.get('text_on_screen')}
        - Audio/Mood: {scene.get('audio_cue')}

        **Global Video Context (for consistency):**
        - Overarching Theme: {global_theme}
        - Global Figures List: {global_figures} 

        Remember: Create a prompt for the *specific scene*, colored by the *global theme*. Only include figures from the global list if they are *in this scene's visual description*.
        """

        # Call the LLM to generate the image prompt
        image_prompt = chat_with_openrouter(prompt_generation_system_prompt, scene_details)

        # Clean up the prompt (e.g., remove potential quotes)
        cleaned_prompt = image_prompt.strip().strip('"')

        generated_prompts.append(cleaned_prompt)
        if os.getenv('DEBUG_LLM') == '1':
            print(f"  - Prompt for Scene {scene.get('scene_number')}: {cleaned_prompt}")

    return {"frame_prompts": generated_prompts}


def check_user_decision(state: GraphState):
    if state["user_decision"] == "Yes":
        return "creative_director"
    else:
        return "brand_strategist"


def check_user_happiness(state: GraphState):
    if state["user_happy"]:
        return "creation_of_scripts"
    else:
        return "creative_director"


if __name__ == "__main__":
    # Build and run the offline workflow only when executing this file directly
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("research_agent", research_agent_node)
    workflow.add_node("brand_strategist", brand_strategist_node)
    workflow.add_node("user_feedback_yes_no", user_feedback_yes_no_node)
    workflow.add_node("creative_director", creative_director_node)
    workflow.add_node("br_feedback", br_feedback_node)
    workflow.add_node("user_feedback_loop", user_feedback_loop_node)
    workflow.add_node("creation_of_scripts", creation_of_scripts_node)
    workflow.add_node("generate_global_themes", generate_global_themes_node)
    workflow.add_node("generate_frame_prompts", generate_frame_prompts_node)

    # Entry and edges
    workflow.set_entry_point("research_agent")
    workflow.add_edge("research_agent", "brand_strategist")
    workflow.add_edge("brand_strategist", "user_feedback_yes_no")
    workflow.add_edge("creative_director", "br_feedback")
    workflow.add_edge("br_feedback", "user_feedback_loop")

    workflow.add_conditional_edges(
        "user_feedback_yes_no",
        check_user_decision,
        {"creative_director": "creative_director", "brand_strategist": "brand_strategist"}
    )
    workflow.add_conditional_edges(
        "user_feedback_loop",
        check_user_happiness,
        {"creation_of_scripts": "creation_of_scripts", "creative_director": "creative_director"}
    )

    workflow.add_edge("creation_of_scripts", "generate_global_themes")
    workflow.add_edge("generate_global_themes", "generate_frame_prompts")
    workflow.add_edge("generate_frame_prompts", END)

    compiled = workflow.compile()

    final_state = compiled.invoke({})
    try:
        print("\nSaving outputs to files...")

        with open("brand_strategy.md", "w", encoding="utf-8") as f:
            f.write(final_state.get('summary_plan_audience', 'No content generated.'))

        with open("creative_concept.md", "w", encoding="utf-8") as f:
            f.write(final_state.get('creative_director_node', 'No content generated.'))

        with open("final_script.json", "w", encoding="utf-8") as f:
            script_data = final_state.get('scripts_created', {})
            json.dump(script_data, f, indent=4)

        with open("global_themes_and_figures.md", "w", encoding="utf-8") as f:
            themes = final_state.get('global_themes_and_figures', {})
            f.write("# Generated Global Themes and Figures\n\n")
            if not themes:
                f.write("No global themes or figures were generated.")
            else:
                f.write(f"**Global Theme:** {themes.get('global_theme', 'N/A')}\n\n")
                f.write(f"**Global Figures:** {themes.get('global_figures', 'N/A')}\n")

        with open("frame_prompts.md", "w", encoding="utf-8") as f:
            prompts = final_state.get('frame_prompts', [])
            f.write("# Generated Frame Prompts (Combined with Globals)\n\n")
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

    try:
        img = compiled.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(img)
        print("\nGraph visualization saved to workflow_graph.png")
    except Exception as e:
        print(f"\nCould not create visualization: {e}")
        print("Install 'pygraphviz' or 'matplotlib' for visualization.")