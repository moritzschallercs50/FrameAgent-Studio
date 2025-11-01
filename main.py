import json
from llm_library import chat_with_openrouter
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any

# 1. Define the state for the graph
# This is required for StateGraph
class GraphState(TypedDict):
    company_info: str
    summary_plan_audience: str
    user_decision: str
    storyline_characters: str
    br_feedback_result: str
    user_happy: bool
    scripts_created: str
    creative_director_node: str

# Define the nodes
def research_agent_node(state: GraphState):
    with open("anthopic.json", "r") as f:
        company_data = json.load(f)

    return {"company_info": company_data}

def brand_strategist_node(state: GraphState):
    # Brand core Brand positioning
    system_prompt = (f"""You are the Brand Strategist AI Agent — a master of understanding businesses, markets, and people. You instinctively see how a product fits into the bigger business picture and how brand storytelling can drive measurable growth. You can instantly adapt your tone and direction — bringing flash and creativity for consumer brands, or polish and authority for B2B companies. You have deep, cross-industry knowledge and can quickly grasp what makes each business unique, whether it’s a tech startup, fashion label, or financial firm.
Your goal is to help the business succeed. Every idea, plan, and observation should serve that purpose. You translate data and company information (received in structured JSON form) into clear strategic insight: what the company stands for, who it needs to reach, and why its message matters. You balance creativity with commercial logic — crafting strategic direction that empowers the creative team to make work that not only looks good but works for the business. Here is the company information: {state}
""")
    return {"summary_plan_audience": chat_with_openrouter(system_prompt)}

def user_feedback_yes_no_node(state: GraphState):
    print("User says: Yes/No")
    # This node represents user interaction
    # In a real graph, this would wait for input and update the state
    return {"user_decision": "Yes"} # Simulate 'Yes'

def creative_director_node(state: GraphState):
    system_prompt = (f"""You are the Creative Director AI Agent — a world-class advertising mind with an instinct 
    for storytelling that moves people and sells ideas. You understand that every great ad begins with understanding
     the audience — what makes them laugh, feel, and care. You know how to capture attention in seconds, using humour, emotion, or clever narrative structure to make a brand unforgettable. Whether it’s a heartfelt story, a viral joke, or an elegant visual metaphor, you know how to make a message resonate.
You work hand-in-hand with the Brand Strategist and the user. The strategist brings the foundation — who the brand is and what it needs to achieve — and you turn that insight into creative magic. You listen closely to feedback, adapt quickly, and collaborate to refine ideas until they feel right for both the brand and the audience. You’re bold but purposeful: your goal isn’t just to make something beautiful — it’s to make something that truly helps the business grow and connect with people. Here is the brand strategy and brand information: {state}
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
    # json output
    system_prompt = (f"""You are the Script Writer AI Agent. Your job is to take the approved creative concept a
    nd write a fully developed video script for a 30 second advertisement. You should think cinematically, 
    translating the creative direction into specific scenes, dialogues, and voiceovers that feel natural and 
    emotionally resonant. Every line should serve a purpose — building the story, highlighting the product, 
    and evoking the desired emotional response. Your script should include scene-by-scene breakdowns, dialogue 
     narration, and stage directions (camera cues, mood, music suggestions if relevant). 
     The tone should match the brand’s voice and target audience, as defined by the strategist and creative director.
      Be concise but vivid — your goal is to write something that’s ready to hand to a video producer or 
      AI video generator.
    Here is the final creative concept and brand information: {state}""")

    return {"scripts_created": chat_with_openrouter(system_prompt)}
# Define conditional logic functions
def check_user_decision(state: GraphState):
    # This function routes after the 'Brand Strategist'
    if state["user_decision"] == "Yes":
        return "creative_director"
    else:
        return "brand_strategist" # Loop back if 'No'

def check_user_happiness(state: GraphState):
    # This function routes after the 'User Feedback (Loop)'
    if state["user_happy"]:
        return "creation_of_scripts"
    else:
        return "creative_director" # Loop back if 'No'

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
workflow.add_edge("creation_of_scripts", END)

# Compile the graph
app = workflow.compile()



final_state = app.invoke({})
try:
    print("\nSaving outputs to Markdown files...")

    # 1. Save Brand Strategist output
    # Access the key 'summary_plan_audience' from the final state
    with open("brand_strategy.md", "w", encoding="utf-8") as f:
        f.write(final_state.get('summary_plan_audience', 'No content generated.'))

    # 2. Save Creative Director output
    # Access the key 'storyline_characters' from the final state
    with open("creative_concept.md", "w", encoding="utf-8") as f:
        f.write(final_state.get('creative_director_node', 'No content generated.'))

    # 3. Save Final Script output
    # Access the key 'scripts_created' from the final state
    with open("final_script.md", "w", encoding="utf-8") as f:
        f.write(final_state.get('scripts_created', 'No content generated.'))

    print("Successfully saved 3 Markdown files.")

except KeyError as e:
    print(f"\nError: A key was missing from the final state: {e}")
except IOError as e:
    print(f"\nError writing files to disk: {e}")
with open("final_state.json", "w") as f:
    json.dump(final_state, f, indent=4)
try:
    img = app.get_graph().draw_mermaid_png()
    with open("workflow_graph.png", "wb") as f:
        f.write(img)
    print("\nGraph visualization saved to workflow_graph.png")
except Exception as e:
    print(f"\nCould not create visualization: {e}")
    print("Install 'pygraphviz' or 'matplotlib' for visualization.")