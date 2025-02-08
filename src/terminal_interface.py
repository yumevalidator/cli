import sys
import os
import readchar

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