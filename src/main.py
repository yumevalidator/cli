import sys
import os
import readchar
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
import webbrowser
import importlib.resources as pkg_resources

from .constants import version
from .testing_agent import start_testing
import threading
import asyncio
import subprocess
import signal

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

def host_report_data():
    class CORSRequestHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()

    print("Current directory:", os.getcwd())
    host_current_directory = os.getcwd()
    os.chdir(host_current_directory + "/.yumevalidator")
    host_handler = CORSRequestHandler
    host_httpd = HTTPServer(('localhost', 9001), host_handler)
    print("Serving on http://localhost:9001 server")
    host_httpd.serve_forever()

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
        start_testing()
        report_process = subprocess.Popen(["yumevalidator", "report"])
        report_process.wait()
        return

    if args == ["report-server"]:
        return host_report_data()
    
    if args == ["report-client"]:
        return display_reporting_screen()

    if args == ["report"]:
        server_process = subprocess.Popen(["yumevalidator", "report-server"])
        client_process = subprocess.Popen(["yumevalidator", "report-client"])

        def cleanup():
            server_process.terminate()
            client_process.terminate()
            server_process.wait()
            client_process.wait()

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGHUP, cleanup)
        signal.signal(signal.SIGQUIT, cleanup)

        server_thread = threading.Thread(target=server_process.wait)
        client_thread = threading.Thread(target=client_process.wait)
        server_thread.start()
        client_thread.start()
        server_thread.join()
        client_thread.join()
        return
    
    if args == ["test_host"]:
        return host_report_data()
    
    print("Command line arguments:", args)

if __name__ == "__main__":
    main() 