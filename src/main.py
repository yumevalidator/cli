import sys
import os
import readchar
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
import webbrowser
import importlib.resources as pkg_resources

package_version = "0.1.0";

def clear_last_lines(num_lines):
    for _ in range(num_lines):
        # Move cursor up one line
        sys.stdout.write("\033[F")
        # Clear the line
        sys.stdout.write("\033[K")

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def draw_menu(options, selected_idx):
    #clear_console()
    for idx, option in enumerate(options):
        prefix = "> " if idx == selected_idx else "  "
        print(f"{prefix}{option}")

def selector_menu(options):
    selected_idx = 0
    while True:
        draw_menu(options, selected_idx)
        key = readchar.readkey()
        if key == readchar.key.UP and selected_idx > 0:
            selected_idx -= 1
            clear_last_lines(len(options))
        elif key == readchar.key.DOWN and selected_idx < len(options) - 1:
            selected_idx += 1
            clear_last_lines(len(options))
        elif key == readchar.key.ENTER:
            return selected_idx

def initialize():
    if os.path.isfile(".yumevalidator.json"):
        overwrite = input("File .yumevalidator.json already exists. Do you want to overwrite it? (y/n): ")
        if overwrite.lower() != 'y':
            return "Initialization cancelled"
    
    figma_token = input("Please enter your Figma token: ")
    
    figma_key = input("Please enter the relevant figma board key: ")
    
    ai_options = ["OpenAI", "Claude"]
    ai_selected = selector_menu(ai_options)
    ai_api_key = input("Please enter your AI API key:")
    with open(".yumevalidator.json", "w") as f:
        json.dump({
            "figma_token": figma_token,
            "figma_key": figma_key,
            "ai_provider": ai_options[ai_selected],
            "ai_api_key": ai_api_key
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
        return "Version " + package_version

    if args == ["init"]:
        return initialize()
    
    if args == ["test"]:
        return "running tests"
    
    if args == ["report"]:
        return display_reporting_screen()
    
    print("Command line arguments:", args)


if __name__ == "__main__":
    main() 