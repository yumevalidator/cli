from smolagents import CodeAgent, OpenAIServerModel

import json
import constants
import figma_functions

def start_testing():
    """start running the figma testing agent"""
    figma_functions.figma_get_all_pages()
    # read from .yumevalidator.json file\
    with open(".yumevalidator.json") as f:
        config = json.load(f)
        model = constants.instruct_openai_model
        # test functionally
