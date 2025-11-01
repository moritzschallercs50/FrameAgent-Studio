import os
import base64
from openai import OpenAI
from typing import List, Optional


def _encode_image_to_base64(image_path: str) -> str:
    """Encodes a local image file into a base64 data URI."""

    # Infer MIME type from the file extension
    extension = image_path.split('.')[-1].lower()
    mime_type = "image/jpeg"  # Default
    if extension == "png":
        mime_type = "image/png"
    elif extension == "webp":
        mime_type = "image/webp"

    # Read the image in binary mode and encode it
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_string}"
    except IOError as e:
        print(f"Error reading image file {image_path}: {e}")
        raise


def chat_with_openrouter(prompt: str, extra_prompt=None, image_paths: Optional[List[str]] = None) -> str:
    """
    Sends a text prompt and optional images to x-ai/grok-4-fast via OpenRouter.

    Args:
        prompt: The text prompt to send to the model.
        image_paths: A list of local file paths to the images.

    Returns:
        The text response from the model.
    """
    if extra_prompt:
        prompt += " " + extra_prompt

    # 1. Get API key from environment variables
    api_key =  "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"
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY environment variable not set.")

    # 2. Initialize the client to point to OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # 3. Build the multimodal message content
    user_content = []

    # Add the text prompt first
    user_content.append({"type": "text", "text": prompt})

    # Add any images
    if image_paths:
        for path in image_paths:
            try:
                # Encode the image and add it to the content list
                base64_image_url = _encode_image_to_base64(path)
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": base64_image_url}
                })
            except Exception as e:
                print(f"Warning: Could not encode image {path}. Skipping. Error: {e}")

    # 4. Create the final messages list
    messages = [
        {
            "role": "user",
            "content": user_content,
        }
    ]

    print("Sending request to Grok-4-fast...")
    try:
        # 5. Send the request
        completion = client.chat.completions.create(
            model="x-ai/grok-4-fast",
            messages=messages,
            max_tokens=1024,  # Set a reasonable limit
        )

        # 6. Return the text content of the response
        return completion.choices[0].message.content

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error: Could not get a response."

def generate_image_with_style(prompt: str, style: str = "TSB Advert") -> Optional[bytes]:
    """
    Generates an image based on a prompt and style using google/gemini-2.5-flash-image.

    Args:
        prompt: The text prompt to guide the image generation.
        style: The style to apply to the image generation. Defaults to "TSB Advert".

    Returns:
        The generated image as bytes, or None if the generation fails.
    """
    # Combine the prompt and style
    full_prompt = f"{prompt} in the style of {style}"

    # 1. Get API key from environment variables
    api_key = "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"
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY environment variable not set.")

    # 2. Initialize the client to point to OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # 3. Build the request payload
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": full_prompt}],
        }
    ]

    print("Sending image generation request to google/gemini-2.5-flash-image...")
    # 4. Send the request
    completion = client.chat.completions.create(
        model="google/gemini-2.5-flash-image",
        messages=messages,
        max_tokens=0,  # No text response expected
    )

    # 5. Extract the image content from the response
    message = completion.choices[0].message
    print(message)

    # The 'message' object has a 'content' attribute which is a LIST
    # We want the first item in that list
    content_part = message.content[0]

    print(content_part)



    # Now you can decode it
    import base64
    return base64.b64decode(content_part)





# Example usage
if __name__ == "__main__":
    prompt = "A futuristic cityscape at sunset"
    style = "Cyberpunk Art"
    image = generate_image_with_style(prompt, style)

    if image:
        with open("generated_image.png", "wb") as f:
            f.write(image)
        print("Image successfully generated and saved as 'generated_image.png'.")
    else:
        print("Image generation failed.")

# --- HOW TO USE THE FUNCTION ---
if __name__ == "__main__":
    # Example 1: Text-only prompt
    print("--- Text-Only Example ---")
    text_prompt = "What is the capital of France?"
    response = chat_with_openrouter(prompt=text_prompt)
    print(f"Prompt: {text_prompt}")
    print(f"Response: {response}\n")

    # Example 2: Text and Image prompt
    print("--- Multimodal (Image) Example ---")
    image_prompt = "What is in this image?"
    image_files = ["test_image.jpg"]  # Make sure this file exists

    try:
        response = chat_with_openrouter(prompt=image_prompt, image_paths=image_files)
        print(f"Prompt: {image_prompt}")
        print(f"Images: {image_files}")
        print(f"Response: {response}")
    except FileNotFoundError:
        print(f"Skipping multimodal example: test_image.jpg not found.")