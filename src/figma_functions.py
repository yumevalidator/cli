# This function is responsible for handling the retrieval of figma-related data from the API
# Functionalities include:
# - Describe the Figma Webpage
# - Generate a list of all interactable elements
# - Obtain screenshot from Figma

import requests
import json
import asyncio

from smolagents import OpenAIServerModel, tool
from openai import OpenAI

import constants
import base64

figma_contents = []

async def figma_get_all_pages():
    """download and update contents from figma into a variable to be processed"""
    with open(".yumevalidator.json") as f:
        config = json.load(f)
        figma_token = config["figma_token"]
        figma_key = config["figma_key"]
        response = requests.get(f"https://api.figma.com/v1/files/{figma_key}", headers={"X-Figma-Token": figma_token})
        data = response.json()
        document_children = data["document"]["children"][0]["children"]
        print(len(document_children))
        figma_contents = document_children

async def figma_print_page(target_page_index):
    """
    print out a specific page from figma and save it as a png file with the name {target_page_id}.png
    """
    with open(".yumevalidator.json") as f:
        config = json.load(f)
        figma_token = config["figma_token"]
        figma_key = config["figma_key"]
        response = requests.get(f"https://api.figma.com/v1/images/{figma_key}?ids={target_page_index}", headers={"X-Figma-Token": figma_token})
        image_url = response.json()["images"][target_page_index]
        image_response = requests.get(image_url)
        with open(f"{target_page_index}.png", "wb") as img_file:
            img_file.write(image_response.content)
            return f"{target_page_index}.png"

async def figma_get_all_interactable_elements_from_node(target_page_index):
    # target_page is a json file that contains information about a figma node
    # repeatable parse the target_page to find all interactable elements
    # interactable elements have non-empty "interactions" field
    interactable_elements = []

    def find_interactable_elements(node):
        stack = [node]
        while stack:
            current_node = stack.pop()
            if "children" in current_node:
                stack.extend(current_node["children"])
            if "interactions" in current_node and current_node["interactions"]:
                interactable_elements.append(current_node["id"])

    find_interactable_elements(figma_contents[target_page_index])
    return interactable_elements

@tool
async def figma_describe_screen(screen_image):
    # describe what the screen is about to be fed into the next agent
    with open(".yumevalidator.json") as f:
        config = json.load(f)
        client = OpenAI(api_key=config["openai_api_key"])
        with open(screen_image, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            img_url = f"data:image/png;base64,{encoded_string}"
            response = client.chat.completions.create(
                model=constants.main_openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "This is a screen of a website. Please describe what you see."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"{img_url}"},
                            },
                        ],
                    }
                ],
            )
            return response


"""
pages = asyncio.run(figma_get_all_pages())
#print(json.dumps(pages[0], indent=4))
screen_file_name = asyncio.run(figma_print_page(pages[0]))
print(screen_file_name)
print(asyncio.run(figma_describe_screen(
    screen_file_name
)))
"""
#print(asyncio.run(figma_get_all_interactable_elements_from_node(pages[0])))
#figma_print_image(pages[0]["id"])


        
