# This function is responsible for handling the retrieval of figma-related data from the API
# Functionalities include:
# - Describe the Figma Webpage
# - Generate a list of all interactable elements
# - Obtain screenshot from Figma

import requests
import json
import asyncio
from io import BytesIO

from smolagents import OpenAIServerModel, tool
from openai import OpenAI
from PIL import Image

from .constants import *

import base64
import os

figma_contents = []
figma_pages = []
interactable_elements_body = []

def get_updated_figma_pages():
    return figma_pages

async def figma_get_all_pages():
    """download and update contents from figma into a variable to be processed"""
    with open(".yumevalidator.json") as f:
        global figma_contents
        global figma_pages
        
        config = json.load(f)
        figma_token = config["figma_token"]
        figma_key = config["figma_key"]
        response = requests.get(f"https://api.figma.com/v1/files/{figma_key}", headers={"X-Figma-Token": figma_token})
        data = response.json()
        document_children = data["document"]["children"][0]["children"]
        print(len(document_children))
        figma_contents = document_children
        figma_pages = [page["id"] for page in document_children]

async def figma_print_target(target_index):
    """
    print out a specific page from figma and save it as a png file with the name {target_page_id}.png
    """
    with open(".yumevalidator.json") as f:
        config = json.load(f)
        figma_token = config["figma_token"]
        figma_key = config["figma_key"]
        response = requests.get(f"https://api.figma.com/v1/images/{figma_key}?ids={target_index}", headers={"X-Figma-Token": figma_token})
        image_url = response.json()["images"][target_index]
        image_response = requests.get(image_url)
        if not os.path.exists("figma"):
            os.makedirs("figma")
        with open(f"figma/{target_index}.png", "wb") as img_file:
            img_file.write(image_response.content)
            return f"{target_index}.png"

def figma_get_all_interactable_elements_from_node(target_page_index):
    # target_page is a json file that contains information about a figma node
    # repeatable parse the target_page to find all interactable elements
    # interactable elements have non-empty "interactions" field
    interactable_elements = []

    def find_interactable_elements(node):
        global interactable_elements_body
        stack = [node]
        while stack:
            current_node = stack.pop()
            if "children" in current_node:
                stack.extend(current_node["children"])
            if "interactions" in current_node and current_node["interactions"]:
                interactable_elements.append(current_node["id"])
                interactable_elements_body.append(current_node)

    target_base_node = [node for node in figma_contents if node["id"] == target_page_index][0]
    find_interactable_elements(target_base_node)
    return interactable_elements

async def figma_describe_screen(screen_image):
    # describe what the screen is about to be fed into the next agent
    with open(".yumevalidator.json") as f:
        config = json.load(f)
        client = OpenAI(api_key=config["openai_api_key"])
        with open(f"figma/{screen_image}", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            img_url = f"data:image/png;base64,{encoded_string}"
            response = client.chat.completions.create(
                model=main_openai_model,
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
            return response.choices[0].message.content

@tool
def figma_get_image(element_id: str) -> BytesIO:
     """
     obtain how a particular element look like on the figma design whether if it is a specific element or an entire page

     Args:
        element_id: the id of the element in question
    Returns:
        the image of the element in bytes
     """
     with open(f"figma/{element_id}.png", "rb") as image_file:
        return Image.open(BytesIO(image_file.read()))

@tool
def figma_get_interaction_target(element_id: str) -> str:
    """
    for a specific element, return the destination interaction target
    Args:
        element_id: the id of the element in question
    Returns:
        the target id of the interaction to be used in get_image to know how it looks like
    """
    target_base_node = [node for node in interactable_elements_body if node["id"] == element_id][0]
    if "interactions" in target_base_node:
        return target_base_node["interactions"][0]["actions"][0]["destinationId"]
    pass

if __name__ == "__main__":
    pages = asyncio.run(figma_get_all_pages())
    #print(json.dumps(pages[0], indent=4))
    screen_file_name = asyncio.run(figma_print_target(figma_pages[0]))
    figma_get_all_interactable_elements_from_node(figma_pages[0])
    #print(json.dump(interactable_elements_body, indent=4)
    print(screen_file_name)
    print(asyncio.run(figma_describe_screen(
        screen_file_name
    )))
    print(asyncio.run(figma_get_interaction_target("1:6")))
    pass
#print(asyncio.run(figma_get_all_interactable_elements_from_node(pages[0])))
#figma_print_image(pages[0]["id"])


        
