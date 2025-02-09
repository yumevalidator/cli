from io import BytesIO
from time import sleep

import helium
import json
import asyncio

from dotenv import load_dotenv
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from smolagents import CodeAgent, tool
from smolagents.agents import ActionStep
from smolagents import CodeAgent, OpenAIServerModel

from .constants import main_model, helium_instructions
from .figma_functions import *
from .difference_image_generator import diff_img

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=1000,1350")
chrome_options.add_argument("--disable-pdf-viewer")
chrome_options.add_argument("--window-position=0,0")

global running_visual_testing_agent
running_visual_testing_agent: CodeAgent = None

global buffered_figma_image
buffered_figma_image = None

global screenshot_image
screenshot_image = None

global visual_testing_summary
visual_testing_summary = []

global current_working_list
current_working_list = []

global current_wrong_list
current_wrong_list = []

global current_recommendations_list
current_recommendation_list = []

global current_page_name
current_page_name = ""

global current_page_id
current_page_id = ""

def start_browser():
    global driver
    driver = helium.start_chrome(headless=False, options=chrome_options)

@tool
def save_screenshot(page_id: str) -> bool:
    """
    description: take a screenshot of the current page and save it to the memory with figma design as the context for comparison
    Args:
        page_id: the id of the page in question
    returns:
        true: screenshot has been saved successfully
        false: screenshot saving failed
    """
    sleep(1.0)  # Let JavaScript animations happen before taking the screenshot
    driver = helium.get_driver()
    if driver is not None:

        global screenshot_image
        global buffered_figma_image

        screenshot_image = (Image.open(BytesIO(driver.get_screenshot_as_png())))
        buffered_figma_image = Image.open(f".yumevalidator/{page_id}.png")

        if not os.path.exists(".yumevalidator"):
            os.makedirs(".yumevalidator")

        screenshot_image.save(f".yumevalidator/screenshot_{page_id}.png")


        return True
    return False

def add_image_to_observation(memory_step: ActionStep, agent: CodeAgent) -> None:
    
    global screenshot_image
    global buffered_figma_image
    global current_page_id

    if screenshot_image is not None and buffered_figma_image is not None:
        #diff_img(current_page_id)
        #memory_step.observations_images = [Image.open(f".yumevalidator/diff_{current_page_id}.png").copy()]
        memory_step.observations_images = [screenshot_image.copy()]
        memory_step.observations_images.append(buffered_figma_image.copy())
        screenshot_image.close()
        buffered_figma_image.close()
        screenshot_image = None
        buffered_figma_image = None

def figma_get_image(element_id: str) -> bool:
    """
     obtain how a particular element look like on the figma design whether if it is a specific element or an entire page
     It will be passed into memory during the next step

     Args:
        element_id: the id of the element in question
    Returns:
        true: image has been retrieved successfully
        false: image retrieval failed
     """
    
    with open(f".yumevalidator/{element_id}.png", "rb") as img_file:
        global buffered_figma_image
        buffered_figma_image = Image.open(BytesIO(img_file.read())).copy()
        print(buffered_figma_image.size)
        return True

@tool
def end_visual_testing(page_title: str, page_id: str) -> str:
    """
    End the testing of the current page
    Args:
        page_title: the human-readable name of the page
        page_id: the id of the page
    Returns:
        status
    """
    global visual_testing_summary
    visual_testing_summary.append(
        {
            "page_title": page_title,
            "page_id": page_id,
            "working": current_working_list,
            "wrong": current_wrong_list,
            "recommendations": current_recommendation_list,
        }
    )
    return "Testing of the current page can be ended successfully"

@tool
def add_to_working_list(title: str, description: str) -> str:
    """
    Record which part of the visual testing is working
    Args:
        title: the title of the working part
        description: the description of the working part
    """
    global current_working_list
    current_working_list.append({
            "title": title,
            "description": description
        })
    return "Working part has been added successfully"

@tool
def add_to_wrong_list(title: str, description: str, target_element_id: str) -> str:
    """
    Record which part of the visual testing is wrong
    Args:
        title: the title of the wrong part
        description: the description of the wrong part
        target_element_id: the id of the element that is wrong (it is the non-human readable token)
    """
    global current_wrong_list
    current_wrong_list.append({
            "title": title,
            "description": description,
            "target_element": target_element_id
        })
    return "Wrong part has been added successfully"

@tool
def add_to_recommendation_list(title: str, description: str) -> str:
    """
    Record the suggestion you would give to fix the issues faced
    Args:
        title: the title of the recommendation
        description: the description of the recommendation
    """
    global current_recommendation_list
    current_recommendation_list.append(
        {
            "title": title,
            "description": description
        })
    return "Recommendation has been added successfully"

def start_visual_testing_agent():
    
    global visual_testing_summary
    global current_working_list
    global current_wrong_list
    global current_recommendation_list
    global current_page_name
    global current_page_id

    visual_testing_summary = []
    current_working_list = []
    current_wrong_list = []
    current_recommendation_list = []
    current_page_name = ""
    current_page_id = ""

    start_browser()
    asyncio.run(figma_get_all_pages())
    with open(".yumevalidator.json") as f:
        global visual_test_untested_user_interface
        visual_test_untested_user_interface = get_updated_figma_pages()
        config = json.load(f)
        model = OpenAIServerModel(main_model, "https://api.openai.com/v1", api_key=config["openai_api_key"])

        for page in visual_test_untested_user_interface:
            current_working_list = []
            current_wrong_list = []
            current_recommendation_list = []

            current_page_id = page
            current_page_name = figma_get_page_name(page)
            asyncio.run(figma_print_target(page))
            interactable_nodes = figma_get_all_interactable_elements_from_node(page)
            #page_description = asyncio.run(figma_describe_screen(f"{page}.png"))
            page_description = ""
            for interactable_node in interactable_nodes:
                asyncio.run(figma_print_target(interactable_node))
            
            # Create the agent
            global running_visual_testing_agent
            running_visual_testing_agent = CodeAgent(
                tools=[save_screenshot, end_visual_testing, add_to_recommendation_list, add_to_wrong_list, add_to_working_list],
                model=model,
                additional_authorized_imports=["helium"],
                step_callbacks=[add_image_to_observation],
                max_steps=8,
                verbosity_level=2,
            )

            # Import helium for the agent
            running_visual_testing_agent.python_executor("from helium import *", running_visual_testing_agent.state)
            #running_visual_testing_agent.python_executor("def print(*args, **kwargs): pass", running_visual_testing_agent.state)
            
            execution_request =f"""
            Your objective is to test the visual fidelity of the react project by looking at the Figma Design Image, and the actual website. 3 or more Context Images will be given, one will the figma design file, one will be the implementation rendered webpage and one will be the fidelity difference image

            The title of the page that needs to be tested at the moment is
            {figma_get_page_name(page)}

            The id of the current page is:
            {page}

            The base website url is:
            {
                config["website_url"]
            }
            Here are the available paths of this website, you can visit them by {config["website_url"]}/[path]'
            ```
            {
                os.listdir("src/app")
            }
            ````<end_code>

            Take these steps step by step to test the interaction functionality, and mention which step you are taking. ONLY test the ones that have been mentioned, just because an element is visible, it is not meant to be tested, because it is still under production. Strictly, do not do multiple steps at one time, because it will crash the browser.
            1. Visit the Website
            2. The path of current website is {driver.current_url}, if it is not the same as {figma_get_page_name(page)}, then switch to the correct page. Note that, the image of the page attached does not represent the current page. Homepage typically lives on "/home" or "/index" or "/"
            3. Take a screenshot of the website
            4. Look at the attached figma design, and website screenshot.
            5. Describe what is right, and record it with add_to_working_list tool (there can be muliples)
            6. Describe what is wrong, and record it with add_to_wrong_list tool (there can be multiples)
            7. Describe what can be improved, and record it with add_to_recommendation_list tool (there can be multiples)
            5. End the test

            If the website is entirely white, it is most likely that you forgot to visit the website after opening the browser. Do not do multiple actions in one settings, because the browser might not load as fast as you think.

            Sometimes, the starting webpage might be different from the actual page you should be trying to test. Switch to the relevant website by using the following code:
            Code:
            ```py
            go_to("{config["website_url"]}/" + [[current target potential page]]")
            ```<end_code>

            This is how the figma file structure looks like. If needed find the relevant elements in the figma file and get their id for whatever use cases
            \"\"\"
            {get_figma_file_structure()}
            \"\"\"

            You can use the tools to determine how the specified element looks like on the page and what is the result of interacting with that particular element.
            
            Even if I say there is "Error in Code Parsing", do not worry about it, because it is just a warning, and it will not affect the testing process.
            
            """

            #execution_request = """
            #Please navigate to https://en.wikipedia.org/wiki/Chicago and give me a sentence containing the word "1992" that mentions a construction accident.
            #"""
            try:
                running_task = running_visual_testing_agent.run(execution_request + helium_instructions)
            except TypeError:
                print("completed")
        
        if not os.path.exists(".yumevalidator"):
            os.makedirs(".yumevalidator")
        with open(".yumevalidator/visual_testing_results.json", "w") as outfile:
            json.dump(visual_testing_summary, outfile, indent=4)