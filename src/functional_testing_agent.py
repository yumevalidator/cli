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
# Configure Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=1000,1350")
chrome_options.add_argument("--disable-pdf-viewer")
chrome_options.add_argument("--window-position=0,0")

global driver
global buffered_figma_image
global functional_testing_summary

buffered_figma_image = None
functional_testing_summary = []

def start_browser():
    global driver
    driver = helium.start_chrome(headless=False, options=chrome_options)

functional_test_untested_user_interface = []

# Set up screenshot callback
def save_screenshot(memory_step: ActionStep, agent: CodeAgent) -> None:
    sleep(1.0)  # Let JavaScript animations happen before taking the screenshot
    driver = helium.get_driver()
    current_step = memory_step.step_number
    if driver is not None:
        for previous_memory_step in agent.memory.steps:  # Remove previous screenshots for lean processing
            if isinstance(previous_memory_step, ActionStep) and previous_memory_step.step_number <= current_step - 2:
                previous_memory_step.observations_images = None
        png_bytes = driver.get_screenshot_as_png()

        image = Image.open(BytesIO(png_bytes))
        print(f"Captured a browser screenshot: {image.size} pixels")
        memory_step.observations_images = [image.copy()]  # Create a copy to ensure it persists

    # Update observations with current URL
    url_info = f"Current url: {driver.current_url}"
    memory_step.observations = (
        "current_website_path=" + url_info
    )

def add_buffered_observations(memory_step: ActionStep, agent: CodeAgent) -> None:
    global buffered_figma_image
    if buffered_figma_image is not None:
        print("Adding buffered Figma image to observations")
        memory_step.observations_images.append(buffered_figma_image.copy())
        buffered_figma_image.close()
        buffered_figma_image = None

@tool
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
def search_item_ctrl_f(text: str, nth_result: int = 1) -> str:
    """
    Searches for text on the current page via Ctrl + F and jumps to the nth occurrence.
    Args:
        text: The text to search for
        nth_result: Which occurrence to jump to (default: 1)
    """
    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
    if nth_result > len(elements):
        raise Exception(f"Match n°{nth_result} not found (only {len(elements)} matches found)")
    result = f"Found {len(elements)} matches for '{text}'."
    elem = elements[nth_result - 1]
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    result += f"Focused on element {nth_result} of {len(elements)}"
    return result

@tool
def go_back() -> None:
    """Goes back to previous page."""
    driver.back()

@tool
def close_popups() -> str:
    """
    Closes any visible modal or pop-up on the page. Use this to dismiss pop-up windows!
    This does not work on cookie consent banners.
    """
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()


@tool
def end_testing_page(page_title: str, is_there_error: bool, testing_description: str) -> str:
    """
    End the testing of the current page
    Args:
        page_title: human-readable name of the page that has beent tested",
        is_there_error: whether if there is an error during the testing
        testing_description: the description of the testing, what has been tested in a organized list, with errors listed out properly
    Returns:
        status
    """
    global functional_testing_summary
    functional_testing_summary.append({
        "page_title": page_title,
        "succeeded": not is_there_error, 
        "description": testing_description
        })
    return "Testing of the current page can be ended successfully"


def start_functional_testing_agent():
    
    global functional_testing_summary
    functional_testing_summary = []
    start_browser()
    asyncio.run(figma_get_all_pages())
    with open(".yumevalidator.json") as f:
        global functional_test_untested_user_interface
        functional_test_untested_user_interface = get_updated_figma_pages()
        config = json.load(f)
        model = OpenAIServerModel(main_model, "https://api.openai.com/v1", api_key=config["openai_api_key"])

        for page in functional_test_untested_user_interface:
            asyncio.run(figma_print_target(page))
            interactable_nodes = figma_get_all_interactable_elements_from_node(page)
            #page_description = asyncio.run(figma_describe_screen(f"{page}.png"))
            page_description = ""
            for interactable_node in interactable_nodes:
                asyncio.run(figma_print_target(interactable_node))
            
            # Create the agent
            agent = CodeAgent(
                tools=[close_popups, search_item_ctrl_f, figma_get_image, figma_get_interaction_target, end_testing_page],
                model=model,
                additional_authorized_imports=["helium"],
                step_callbacks=[save_screenshot, add_buffered_observations],
                max_steps=20,
                verbosity_level=2,
            )
            # Import helium for the agent
            agent.python_executor("from helium import *", agent.state)
            
            execution_request =f"""
            Your objective is to test the functionality of the react project by looking at the Figma Design Image, and interacting with the specified elements on the page.
            It might lead you to a different webpage, but you should always try to go back to the original webpage to finish testing the elements on that page.

            The title of the page that needs to be tested at the moment is
            {figma_get_page_name(page)}


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

            Take these steps step by step to test the interaction functionality. ONLY test the ones that have been mentioned, just because an element is visible, it is not meant to be tested, because it is still under production. Strictly, do not do multiple steps at one time, because it will crash the browser.
            1. Visit the Website
            2. The path of current website is {driver.current_url}, if it is not the same as {figma_get_page_name(page)}, then switch to the correct page. Note that, the image of the page attached does not represent the current page.
            3. Look into the interactable_nodes, one after one, do not look into random ones, because they have not been implemented
            4. Use the tool to retrieve the image of the element that is currently being processed
            4. Look at where they lead to
            5. Interact with the element
            6. Check whether if they go to the correct page as intended
            7. Go back to original webpage
            8. After every elements has been checked, end the test for this screen

            If the website is entirely white, it is most likely that you forgot to visit the website after opening the browser. Do not do multiple actions in one settings, because the browser might not load as fast as you think.

            Sometimes, the starting webpage might be different from the actual page you should be trying to test. Switch to the relevant website by using the following code:
            Code:
            ```py
            go_to("{config["website_url"]}/" + [[current target potential page]]")
            ````<end_code>

            You can use the tools to determine how the specified element looks like on the page and what is the result of interacting with that particular element.

            Here is the array of interactable elements on the page in a python array
            Code:
            ```py
            {interactable_nodes}
            ````<end_code>
            
            Here is the description of the current page:
            '
            {page_description}
            '


            #execution_request = """
            #Please navigate to https://en.wikipedia.org/wiki/Chicago and give me a sentence containing the word "1992" that mentions a construction accident.
            #"""
            try:
                agent.run(execution_request + helium_instructions)
            except TypeError:
                print("completed")
    if not os.path.exists(".yumevalidator"):
        os.makedirs(".yumevalidator")
    with open(".yumevalidator/visual_testing_results.json", "w") as outfile:
        json.dump(functional_testing_summary, outfile, indent=4)

if __name__ == "__main__":        
    start_functional_testing_agent()