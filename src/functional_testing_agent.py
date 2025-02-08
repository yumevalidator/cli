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

from .constants import main_openai_model, helium_instructions
from .figma_functions import *
# Configure Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=1000,1350")
chrome_options.add_argument("--disable-pdf-viewer")
chrome_options.add_argument("--window-position=0,0")

global driver

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
        url_info if memory_step.observations is None else memory_step.observations + "\n" + url_info
    )

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


def start_functional_testing_agent():
    start_browser()
    asyncio.run(figma_get_all_pages())
    with open(".yumevalidator.json") as f:
        global functional_test_untested_user_interface
        functional_test_untested_user_interface = get_updated_figma_pages()
        config = json.load(f)
        model_id = main_openai_model
        model = OpenAIServerModel(model_id, "https://api.openai.com/v1", api_key=config["openai_api_key"])

        for page in functional_test_untested_user_interface:
            print("hmm")
            asyncio.run(figma_print_target(page))
            interactable_nodes = figma_get_all_interactable_elements_from_node(page)
            page_description = asyncio.run(figma_describe_screen(f"{page}.png"))
            for interactable_node in interactable_nodes:
                asyncio.run(figma_print_target(interactable_node))
            
            # Create the agent
            agent = CodeAgent(
                tools=[go_back, close_popups, search_item_ctrl_f, figma_get_image, figma_get_interaction_target],
                model=model,
                additional_authorized_imports=["helium"],
                step_callbacks=[save_screenshot],
                max_steps=20,
                verbosity_level=2,
            )
            # Import helium for the agent
            agent.python_executor("from helium import *", agent.state)
            
            execution_request =f"""
            Your objective is to test the functionality of the website by looking at the Figma Design Image, and interacting with the specified elements on the page.
            It might lead you to a different webpage, but you should always try to go back to the original webpage to finish testing the elements on that page.

            If the website is entirely white, it is most likely that you forgot to visit the website after opening the browser. Do not do multiple actions in one settings, because the browser might not load as fast as you think.

            The website you need to visit is:
            {
                config["website_url"]
            }

            You can use the tools to determine how the specified element looks like on the page and what is the result of interacting with that particular element.

            Here is the array of interactable elements on the page in a python array
            Code:
            ```py
            {interactable_nodes}
            ```
            
            Here is the description of the current page:
            `
            {page_description}
            `
            """

            #execution_request = """
            #Please navigate to https://en.wikipedia.org/wiki/Chicago and give me a sentence containing the word "1992" that mentions a construction accident.
            #"""

            agent_output = agent.run(execution_request + helium_instructions)
            print("Final output:")
            print(agent_output)

if __name__ == "__main__":        
    start_functional_testing_agent()