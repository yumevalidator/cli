import sys
import os
import readchar

package_version = "0.1.0";

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def draw_menu(options, selected_idx):
    clear_console()
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
        elif key == readchar.key.DOWN and selected_idx < len(options) - 1:
            selected_idx += 1
        elif key == readchar.key.ENTER:
            return selected_idx

def main():
    args = sys.argv[1:]
    if not args:
        raise ValueError("No command line arguments provided.")
    
    if args == ["version"]:
        return "Version " + package_version

    if args == ["init"]:
        if os.path.isfile(".yumevalidator.json"):
            overwrite = input("File .yumevalidator.json already exists. Do you want to overwrite it? (y/n): ")
            if overwrite.lower() != 'y':
                return "Initialization cancelled."
        options = ["Option 1", "Option 2", "Option 3", "Exit"]
        selected = selector_menu(options)
        print(f"You selected: {options[selected]}")
        options = ["Option 1", "Option 2", "Option 3", "Exit"]
        selected = selector_menu(options)
        return "initialzing project"
    
    if args == ["test"]:
        return "running tests"
    print("Command line arguments:", args)


if __name__ == "__main__":
    main() 