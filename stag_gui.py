#!/usr/bin/env python3

############################################################
## stag_gui                                                #
## Simple GUI for Stephan's Automatic Image Tagger         #
############################################################


import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import sys

import huggingface_hub
from PIL import Image, ImageTk
import webbrowser
from stag import SKTagger
from tktooltip import ToolTip
from huggingface_hub import hf_hub_download



class TextRedirector:
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, out_str):
        self.text_widget.insert(tk.END, out_str, (self.tag,))
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()

    def flush(self):
        pass

stop_event = threading.Event()

def run_tagger():
    stop_event.clear()
    update_ui_state(running=True)

    imagedir = entry_imagedir.get()
    prefix = entry_prefix.get() or 'st'
    force = not var_skip.get()
    test = var_test.get()
    prefer_exact_filenames = var_prefer_exact_filenames.get()

    threading.Thread(target=run_tagger_directly, args=(imagedir, prefix, force, test, prefer_exact_filenames, stop_event)).start()

def run_tagger_directly(imagedir, prefix, force, test, prefer_exact_filenames, stop_event):
    sys.stdout = TextRedirector(text_output, "stdout")
    sys.stderr = TextRedirector(text_output, "stderr")

    print("Starting tagger...")

    # check if model was already downloaded
    dl_dir = os.path.join(huggingface_hub.constants.HF_HUB_CACHE,"models--xinyu1205--recognize-anything-plus-model")
    if not os.path.isdir(dl_dir):
        show_startup_alert()

    pretrained = hf_hub_download(repo_id="xinyu1205/recognize-anything-plus-model", filename="ram_plus_swin_large_14m.pth")

    tagger = SKTagger(pretrained, 384, force, test, prefer_exact_filenames, prefix)

    if not stop_event.is_set():
        tagger.enter_dir(imagedir, stop_event)

    print("The mighty STAG has done its work. Have a nice day.")

    # After the tagger finishes or is cancelled
    update_ui_state(running=False)

def cancel_tagger():
    print("Cancelling tagger...")
    stop_event.set()

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        entry_imagedir.delete(0, tk.END)
        entry_imagedir.insert(0, directory)

def update_ui_state(running):
    if running:
        entry_imagedir.config(state='disabled')
        entry_prefix.config(state='disabled')
        browse_button.config(state='disabled')
        run_button.config(state='disabled')
        cancel_button.config(state='normal')
        force_checkbox.config(state='disabled')
        test_checkbox.config(state='disabled')
        prefer_exact_filenames_checkbox.config(state='disabled')
    else:
        entry_imagedir.config(state='normal')
        entry_prefix.config(state='normal')
        browse_button.config(state='normal')
        run_button.config(state='normal')
        cancel_button.config(state='disabled')
        force_checkbox.config(state='normal')
        test_checkbox.config(state='normal')
        prefer_exact_filenames_checkbox.config(state='normal')

def open_webpage(url):
    webbrowser.open_new(url)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def show_startup_alert():
    messagebox.showinfo("Welcome to STAG", "In order to be able to tag your images, STAG now needs to download "
    "the recognize-anything model from huggingface. This might take a while and is perfectly normal. The download "
    "is only done once, so the next time you start STAG you will be ready to go in an instant.")


if __name__ == '__main__':

    version_identifier = "1.0.0"

    img_dir = resource_path("images")
    divisio_logo_file = os.path.join(img_dir, "divisio_design-assets_logo_schwarz_WEB.png")
    stag_logo_file = os.path.join(img_dir, "stag_logo.png")
    divisio_logo_image = Image.open(divisio_logo_file)
    stag_logo_image = Image.open(stag_logo_file)

    root = tk.Tk()
    root.title("DIVISIO STAG")

    original_size = divisio_logo_image.size
    new_size = (int(original_size[0] * 0.5), int(original_size[1] * 0.5))
    divisio_logo_image= divisio_logo_image.resize(new_size)

    original_size = stag_logo_image.size
    new_size = (int(original_size[0] * 0.5), int(original_size[1] * 0.5))
    stag_logo_image= stag_logo_image.resize(new_size)

    # Create a frame to contain the logo and version text
    logo_frame = ttk.Frame(root)
    logo_frame.grid(row=6, rowspan=4, column=0, padx=5, pady=5, sticky='sw')

    # Load and display the logo
    stag_logo_photo = ImageTk.PhotoImage(stag_logo_image)
    stag_logo_label = ttk.Label(logo_frame, image=stag_logo_photo)
    stag_logo_label.pack()

    # Add the version text centered below the logo
    version_label = ttk.Label(logo_frame, text="Version "+version_identifier)
    version_label.pack()


    divisio_logo_photo = ImageTk.PhotoImage(divisio_logo_image)
    logo_label = ttk.Label(root, image=divisio_logo_photo)
    logo_label.grid(row=7, column=2, padx=5, pady=5, sticky='ne')

    # Add a label for the creator text
    creator_label = ttk.Label(root, text="Made with love by DIVISIO")
    creator_label.grid(row=8, column=2, padx=5, pady=5, sticky='ne')

    # Add a hyperlink to the webpage
    link = ttk.Label(root, text="Visit our website", foreground="blue", cursor="hand2")
    link.grid(row=9, column=2, padx=5, pady=5, sticky='ne')
    link.bind("<Button-1>", lambda e: open_webpage("https://divis.io"))

    root.columnconfigure(1, weight=1)
    root.rowconfigure(5, weight=1)

    ttk.Label(root, text="Image Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    entry_imagedir = ttk.Entry(root, width=50)
    entry_imagedir.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    browse_button = ttk.Button(root, text="Browse", command=browse_directory)
    browse_button.grid(row=0, column=2, padx=5, pady=5)

    ttk.Label(root, text="Prefix:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    entry_prefix = ttk.Entry(root, width=50)
    entry_prefix.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    entry_prefix.insert(0, "st")

    var_skip = tk.BooleanVar()
    var_skip.set(True)
    force_checkbox = ttk.Checkbutton(root, text="Skip images already tagged by STAG", variable=var_skip)
    force_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    ToolTip(force_checkbox, msg='''If this box is checked, STAG doesn't tag images which
    already have one or more tags with the given prefix.''')

    var_test = tk.BooleanVar()
    test_checkbox = ttk.Checkbutton(root, text="Simulate tagging only", variable=var_test)
    test_checkbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    ToolTip(test_checkbox, msg='''Analyze images but don't write changes to the file system.''')

    var_prefer_exact_filenames = tk.BooleanVar()
    prefer_exact_filenames_checkbox = ttk.Checkbutton(root, text="Use darktable-compatible filenames", variable=var_prefer_exact_filenames)
    prefer_exact_filenames_checkbox.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
    ToolTip(prefer_exact_filenames_checkbox, msg='''When creating new XMP files, create PICT0001.JPG.XMP instead of PICT0001.XMP ''')

    run_button = ttk.Button(root, text="Run STAG", command=run_tagger)
    run_button.grid(row=3, column=0, pady=10)
    cancel_button = ttk.Button(root, text="Cancel", command=cancel_tagger)
    cancel_button.grid(row=3, column=1, pady=10)

    ttk.Label(root, text="Tagger Output:").grid(row=4, column=0, columnspan=3, padx=5, pady=(10, 0), sticky=tk.W)

    text_frame = ttk.Frame(root)
    text_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    text_output = tk.Text(text_frame, height=15, wrap="word")
    text_output.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(text_frame, command=text_output.yview)
    scrollbar.grid(row=0, column=1, sticky='ns')
    text_output['yscrollcommand'] = scrollbar.set

    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    cancel_button.config(state='disabled')

    root.mainloop()
