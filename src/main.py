import sys
import os
import readchar
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
import webbrowser
import importlib.resources as pkg_resources

from .constants import version
from .functional_testing_agent import start_functional_testing_agent

def initialize():
    if os.path.isfile(".yumevalidator.json"):
        overwrite = input("File .yumevalidator.json already exists. Do you want to overwrite it? (y/n): ")
        if overwrite.lower() != 'y':
            return "Initialization cancelled"
    
    figma_token = input("Please enter your Figma token: ")
    figma_key = input("Please enter the relevant figma board key: ")
    openai_api_key = input("Please enter your OpenAI API key:")
    website_url = input("Please enter the website URL you want to validate: ")

    with open(".yumevalidator.json", "w") as f:
        json.dump({
            "figma_token": figma_token,
            "figma_key": figma_key,
            "openai_api_key": openai_api_key,
            "website_url": website_url
        }, f, indent=4)
    
    with open(".gitignore") as f:
        if ".yumevalidator.json" not in f.read():
            with open(".gitignore", "a") as f:
                f.write("\n.yumevalidator.json")
        
    return "initialzing project"

def display_reporting_screen():
    with pkg_resources.path(__package__, 'public') as public_dir:
        print(public_dir)
        os.chdir(public_dir)
        handler = SimpleHTTPRequestHandler
        httpd = HTTPServer(('localhost', 9000), handler)
        print("Serving on http://localhost:9000")
        webbrowser.open("http://localhost:9000")
        httpd.serve_forever()

def main():
    args = sys.argv[1:]
    if not args:
        raise ValueError("No command line arguments provided.")
    
    if args == ["version"]:
        return "Version " + version

    if args == ["init"]:
        return initialize()
    
    if args == ["test"]:
        start_functional_testing_agent()
        return
    
    if args == ["report"]:
        return display_reporting_screen()
    
    print("Command line arguments:", args)

if __name__ == "__main__":
    main() 