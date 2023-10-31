import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import json
from pathlib import Path
# from os.path import join


ctk.set_appearance_mode("system")  # Modes: system (default), light, dark
# ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green
ctk.set_default_color_theme("./orange.json")

tablabels = {"color":"Finding Colors", "remap":"Remapping", "render":"Render", "tartan":"Tartan"}

# Globals
colors_description = "Find a number of common colors in an image.\n - print their RGB values and save a 'Color swatch' for visual reference.\nThe Swatch can be used in the remap tool, or as a visual reference."
initial_color_count = 8
#
remap_description = "Jacquard workflow: Reduce the number of colors in an image.\n - Use a count, and optionally colors defined in a colorref-image. See 'Finding Colors' tab.\n - can also scale width, and rescale height using aspect ratio.\nThe 'colorref-image' can have override colors in bottom of each swatch color block.\nThis will replace the color found in the top with a new color defined in the bottom 1/3 of each block."
initial_remap_width = 4320
initial_remap_aspect = "22/72"
#
render_description = "Render the WIF file into an image format.\n - Vector (SVG) is supported for publication. Raster files are smaller.\n - Can show as liftplan, structure, or highlight long floats.\n - Many visual styles are supported."
initial_floats_count = 5


def load_styles():
    """
    gather the styles for dropdowns
    """
    with open(Path.home() / "Documents" / ".pyweaving" / "styles.json") as inf:
        data = json.load(inf)
        result = data.keys()
    return list(result)

def sizeof(lines):
    """
    Guess at height of lines in description to size frame adequately.
    - Roboto font (in themes) is 13 px high.
    """
    count = lines.count("\n")
    linesize = 13 + 4 # line height + interline spacing (est)
    return (count + 1)*linesize + 10 # padding


class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Create tabs
        for name in tablabels:
            self.add(tablabels[name])
        # Add widgets on tabs
        # Colors Tab
        self.c_desc = ctk.CTkTextbox(master=self.tab(tablabels["color"]), height=sizeof(colors_description))
        self.c_desc.grid(row=0, column=0, padx=5, pady=5, columnspan=5, sticky="new")
        self.c_desc.configure(wrap="word", border_width=0)
        self.c_desc.insert("0.0", colors_description)
        # self.tab(tablabels["color"]).rowconfigure(0, weight=1)
        self.tab(tablabels["color"]).columnconfigure(3, weight=1)
        #
        self.c_label = ctk.CTkLabel(master=self.tab(tablabels["color"]),text="Target Image:")
        self.c_label.grid(row=1, column=0, padx=5, pady=5, sticky="ne")
        self.c_imagefile_btn = ctk.CTkButton(master=self.tab(tablabels["color"]), text="select file", command=self.get_image_file)
        self.c_imagefile_btn.configure(anchor="w")
        self.c_imagefile_btn.grid(row=1, column=1, padx=2, pady=5, columnspan=4, sticky="new")
        self.clabel = ctk.CTkLabel(master=self.tab(tablabels["color"]), text="Colors to find:")
        self.clabel.grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        self.centry = ctk.CTkEntry(master=self.tab(tablabels["color"]), width=40)
        self.centry.insert(0, initial_color_count)
        self.centry.grid(row=2, column=1, padx=5, pady=5, sticky="nw")
        self.c_count = ctk.CTkSlider(master=self.tab(tablabels["color"]), from_=2, to=32, command=self.count_slider_event)
        self.c_count.grid(row=2, column=2, padx=2, pady=5, sticky="new")
        self.c_count.set(initial_color_count)
        #
        self.c_perform = ctk.CTkButton(master=self.tab(tablabels["color"]), text="Perform Action", command=self.do_colors)
        self.c_perform.grid(row=3, column=2, padx=2, pady=5, sticky="e")

        # Remap Tab
        # imagefile, count, colref, filter, width,aspect
        self.re_desc = ctk.CTkTextbox(master=self.tab(tablabels["remap"]), height=sizeof(remap_description))
        self.re_desc.grid(row=0, column=0, padx=5, pady=5, columnspan=5, sticky="new")
        self.re_desc.configure(wrap="word")
        self.re_desc.insert("0.0", remap_description)
        self.tab(tablabels["remap"]).columnconfigure(3, weight=1) # Keep description full width
        # self.tab(tablabels["remap"]).rowconfigure(1, weight=1)
        #
        self.re_label1 = ctk.CTkLabel(master=self.tab(tablabels["remap"]),text="Target Image:")
        self.re_label1.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.re_imagefile_btn = ctk.CTkButton(master=self.tab(tablabels["remap"]), text="select file", command=self.get_image_file)
        self.re_imagefile_btn.configure(anchor="w")
        self.re_imagefile_btn.grid(row=1, column=1, padx=2, pady=5, columnspan=4, sticky="new")
        # Frame: count
        self.re_label2 = ctk.CTkLabel(master=self.tab(tablabels["remap"]), text="Colors to find:")
        self.re_label2.grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        self.re_entry = ctk.CTkEntry(master=self.tab(tablabels["remap"]), width=40)
        self.re_entry.insert(0, initial_color_count)
        self.re_entry.grid(row=2, column=1, padx=5, pady=5, sticky="nw")
        self.re_count = ctk.CTkSlider(master=self.tab(tablabels["remap"]), from_=2, to=32, command=self.count_slider_event)
        self.re_count.grid(row=2, column=2, padx=2, pady=5, sticky="new")
        self.re_count.set(initial_color_count)
        # colorref image
        self.re_ref_check_var = ctk.IntVar(value=0)
        self.re_ref_check = ctk.CTkCheckBox(master=self.tab(tablabels["remap"]), text="Use colorref image:", command=self.check_refcolor,
                                            variable=self.re_ref_check_var, onvalue=1, offvalue=0)
        self.re_ref_check.grid(row=3, column=0, padx=2, pady=5, sticky="nw")
        self.re_reffile_btn = ctk.CTkButton(master=self.tab(tablabels["remap"]), text="select 'colorref' swatch file", command=self.get_reffile)
        self.re_reffile_btn.configure(anchor="w")
        self.re_reffile_btn.grid(row=3, column=1, padx=2, pady=5, columnspan=4, sticky="new")
        # Width and Aspect
        self.re_width_check_var = ctk.IntVar(value=0)
        self.re_aspect_check_var = ctk.IntVar(value=0)
        self.re_width_check = ctk.CTkCheckBox(master=self.tab(tablabels["remap"]), text="Change Width:",
                                              variable=self.re_width_check_var, onvalue=1, offvalue=0)
        self.re_width_check.grid(row=4, column=0, padx=2, pady=5, sticky="nw")
        self.re_width_entry = ctk.CTkEntry(master=self.tab(tablabels["remap"]), width=50) #placeholder_text="Count"
        self.re_width_entry.insert(0, initial_remap_width)
        self.re_width_entry.grid(row=4, column=1, padx=5, pady=5, sticky="nw")
        self.re_aspect_check = ctk.CTkCheckBox(master=self.tab(tablabels["remap"]), text="Change Aspect (PPI/EPI):",
                                              variable=self.re_aspect_check_var, onvalue=1, offvalue=0)
        self.re_aspect_check.grid(row=5, column=0, padx=2, pady=5, sticky="nw")
        self.re_aspect_entry = ctk.CTkEntry(master=self.tab(tablabels["remap"]), width=80) #placeholder_text="Count"
        self.re_aspect_entry.insert(0, initial_remap_aspect)
        self.re_aspect_entry.grid(row=5, column=1, padx=5, pady=5)#, sticky="nw")
        # filter yes/no
        self.filter_check_var = ctk.IntVar(value=0)
        self.re_filter = ctk.CTkCheckBox(master=self.tab(tablabels["remap"]), text="Filter Isolated pixels away",
                                         variable=self.filter_check_var, onvalue=1, offvalue=0)
        self.re_filter.grid(row=4, column=2, padx=2, pady=5, sticky="e")
        # Perform
        self.re_perform = ctk.CTkButton(master=self.tab(tablabels["remap"]), text="Perform Action", command=self.do_remap)
        self.re_perform.grid(row=6, column=2, padx=2, pady=5, sticky="e")
        
        # Render tab
        self.rn_desc = ctk.CTkTextbox(master=self.tab(tablabels["render"]), height=sizeof(remap_description))
        self.rn_desc.grid(row=0, column=0, padx=5, pady=5, columnspan=5, sticky="new")
        self.rn_desc.configure(wrap="word")
        self.rn_desc.insert("0.0", render_description)
        self.tab(tablabels["render"]).columnconfigure(3, weight=1) # Keep description full width
        self.rn_label1 = ctk.CTkLabel(master=self.tab(tablabels["render"]),text="WIF file:")
        self.rn_label1.grid(row=1, column=0, padx=5, pady=5, sticky="ne")
        self.rn_wif_btn = ctk.CTkButton(master=self.tab(tablabels["render"]), text="select file", command=self.get_wif_file)
        self.rn_wif_btn.configure(anchor="w")
        self.rn_wif_btn.grid(row=1, column=1, padx=2, pady=5, columnspan=4, sticky="new")
        # Style
        style_options = load_styles()
        self.rn_label1 = ctk.CTkLabel(master=self.tab(tablabels["render"]), text="Style:")
        self.rn_label1.grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        self.rn_style = ctk.CTkComboBox(master=self.tab(tablabels["render"]), values=style_options)
        self.rn_style.grid(row=2, column=1, padx=2, pady=5, columnspan=2, sticky="nw")
        # Output autopng|autosvg|None 0|1|2
        self.rn_outlabel = ctk.CTkLabel(master=self.tab(tablabels["render"]),text="Resulting Image file:")
        self.rn_outlabel.grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.rn_radio_var = tk.IntVar(value=0)
        self.radio_0 = ctk.CTkRadioButton(master=self.tab(tablabels["render"]), text="AutoPNG", variable= self.rn_radio_var, value=0)
        self.radio_1 = ctk.CTkRadioButton(master=self.tab(tablabels["render"]), text="AutoSVG", variable= self.rn_radio_var, value=1)
        self.radio_2 = ctk.CTkRadioButton(master=self.tab(tablabels["render"]), text="None(popup)", variable= self.rn_radio_var, value=2)
        self.radio_0.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.radio_1.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.radio_2.grid(row=3, column=2, padx=5, pady=5, sticky="e")
        # Floats
        self.rn_floats_check_var = ctk.IntVar(value=0)
        self.rn_floats = ctk.CTkCheckBox(master=self.tab(tablabels["render"]), text="Show floats", command=self.show_floats,
                                         variable=self.rn_floats_check_var, onvalue=1, offvalue=0)
        self.rn_floats.grid(row=4, column=0, padx=2, pady=5, sticky="w")
        self.rn_label2 = ctk.CTkLabel(master=self.tab(tablabels["render"]), text="Floats length:")
        self.rn_label2.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.rn_entry = ctk.CTkEntry(master=self.tab(tablabels["render"]), width=40)
        self.rn_entry.insert(0, initial_floats_count)
        self.rn_entry.grid(row=4, column=1, padx=5, pady=5, sticky="e")
        self.rn_count = ctk.CTkSlider(master=self.tab(tablabels["render"]), from_=2, to=10, command=self.count_slider_event)
        self.rn_count.grid(row=4, column=2, padx=2, pady=5, sticky="ew")
        self.rn_count.set(initial_floats_count)
        # liftplan yes/no
        self.rn_liftplan_check_var = ctk.IntVar(value=0)
        self.rn_liftplan = ctk.CTkCheckBox(master=self.tab(tablabels["render"]), text="Show as a liftplan",
                                         variable=self.rn_liftplan_check_var, onvalue=1, offvalue=0)
        self.rn_liftplan.grid(row=5, column=0, padx=2, pady=5, sticky="nw")
        # structure yes/no
        self.rn_structure_check_var = ctk.IntVar(value=0)
        self.rn_structure = ctk.CTkCheckBox(master=self.tab(tablabels["render"]), text="Show structure only(B&W)",
                                         variable=self.rn_structure_check_var, onvalue=1, offvalue=0)
        self.rn_structure.grid(row=5, column=1, padx=2, pady=5, sticky="nw")
        # Perform
        self.re_perform = ctk.CTkButton(master=self.tab(tablabels["render"]), text="Perform Action", command=self.do_render)
        self.re_perform.grid(row=6, column=2, padx=2, pady=5, sticky="e")
        
        # next tab!
        
        
# self.re_countlabel = ctk.CTkLabel(master=self.tab(tablabels["remap"]),text="Target Image:")
# self.re_countlabel.grid(row=2, column=0, padx=5, pady=5, sticky="nw")
# self.re_colframe = ctk.CTkFrame(master=self.tab(tablabels["remap"]),border_width=2)
# self.re_colframe.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
# self.re_colframe.rowconfigure(0, weight=1)
# self.re_colframe.columnconfigure(0, weight=1)
# self.re_radio_var = tk.IntVar(value=1)
# self.radio_1 = ctk.CTkRadioButton(self.re_colframe, text="count",
                                     # command=self.choose_count_file, variable= self.re_radio_var, value=1)
# self.radio_2 = ctk.CTkRadioButton(self.re_colframe, text="refcolor image",
                                     # command=self.choose_count_file, variable= self.re_radio_var, value=2)
# self.radio_1.grid(row=0, column=0, padx=5, pady=5, sticky="ne")
# self.radio_2.grid(row=1, column=0, padx=5, pady=5, sticky="ne")

        
    def count_slider_event(self, value):
        activetab = self.get()
        if activetab == tablabels["color"]:
            self.centry.delete(0, "end")
            self.centry.insert(0, int(value))
        elif activetab == tablabels["remap"]:
            self.re_entry.delete(0, "end")
            self.re_entry.insert(0, int(value))
        elif activetab == tablabels["render"]:
            self.rn_entry.delete(0, "end")
            self.rn_entry.insert(0, int(value))

    def check_refcolor(self):
        " disable refcolor_im if off "
        if self.re_ref_check_var.get()==0:
            self.re_reffile_btn.configure(state="disabled")
        else:
            self.re_reffile_btn.configure(state="normal")

    def show_floats(self):
        if self.rn_floats_check_var.get()==0:
            self.rn_count.configure(state="disabled")
        else:
            self.rn_count.configure(state="normal")
        
    def get_image_file(self):
        """
        Often an image file is needed.
        """
        # User chooses image file
        filetypes = (('png files', '*.png'),('jpg files', '*.jpg'),('bmp files', '*.bmp'),('All files', '*.*'))
        path = ctk.filedialog.askopenfilename(initialdir='.\\', title='Choose an Image', filetypes=filetypes)
        # Which tab is active and so fill in correct field
        activetab = self.get()
        if activetab == tablabels["color"]:
            self.c_imagefile_btn.configure(text=path)
        elif activetab == tablabels["remap"]:
            self.re_imagefile_btn.configure(text=path)

    def get_reffile(self):
        """
        Occasionally a second file is needed
        """
        filetypes = (('png files', '*.png'),('jpg files', '*.jpg'),('bmp files', '*.bmp'),('All files', '*.*'))
        path = ctk.filedialog.askopenfilename(initialdir='.\\', title='Choose a file', filetypes=filetypes)
        self.re_reffile_btn.configure(text=path)
        activetab = self.get()

    def get_wif_file(self):
        filetypes = (('wif files', '*.wif'),('All files', '*.*'))
        path = ctk.filedialog.askopenfilename(initialdir='.\\', title='Choose a WIF file', filetypes=filetypes)
        # Which tab is active and so fill in correct field
        activetab = self.get()
        if activetab == tablabels["render"]:
            self.rn_wif_btn.configure(text=path)
        
    def do_colors(self):
        """
        Perform simple checks and run
        """
        if self.feedback.get('0.0'):
            self.feedback.delete('0.0', "end")
        contents = self.c_imagefile_btn.cget("text")
        if contents == "select file" or contents == "":
            self.feedback.insert("0.0", "Choose an image file to find colors inside")
        else:
            p = subprocess.run(['pyweaving', 'colors', '--count',self.centry.get(), contents], capture_output=True, text=True)
            self.feedback.insert("0.0", p.stderr)
            self.feedback.insert("end", p.stdout)
        
    def do_remap(self):
        """
        Perform simple checks and run
        """
        if self.feedback.get('0.0'):
            self.feedback.delete('0.0', "end")
        contents = self.re_imagefile_btn.cget("text")
        if contents == "select file" or contents == "":
            self.feedback.insert("0.0", "Choose an image file; to remap colors inside")
        else:
            command = ['pyweaving', 'remap', contents, '--count',self.re_entry.get()]
            if self.re_ref_check_var.get()==1:
                command.extend(['--colref', self.re_reffile_btn.cget("text")])
            if self.re_width_check_var.get()==1:
                command.extend(['--width', self.re_width_entry.get()])
            if self.re_aspect_check_var.get()==1:
                command.extend(['--aspect', self.re_aspect_entry.get()])
            if self.filter_check_var.get()==1:
                command.append('--filter')
            #
            p = subprocess.run(command, capture_output=True, text=True)
            self.feedback.insert("0.0", p.stderr)
            self.feedback.insert("end", p.stdout)

    def do_render(self):
        """
        """
        if self.feedback.get('0.0'):
            self.feedback.delete('0.0', "end")
        contents = self.rn_wif_btn.cget("text")
        if contents == "select file" or contents == "":
            self.feedback.insert("0.0", "Choose a wif file to Render a draft from.")
        else:
            outfile = 'autopng'
            if self.rn_radio_var.get() == 2:
                outfile = ""
            elif self.rn_radio_var.get() == 1:
                outfile = "autosvg"
            command = ['pyweaving', 'render', contents, outfile, '--style', self.rn_style.get()]
            if self.rn_liftplan_check_var.get() == 1:
                command.append('--liftplan')
            if self.rn_structure_check_var.get() == 1:
                command.append('--structure')
            if self.rn_floats_check_var.get() == 1:
                command.extend(['--floats', self.rn_entry.get()])
            #
            p = subprocess.run(command, capture_output=True, text=True)
            self.feedback.insert("0.0", p.stderr)
            self.feedback.insert("end", p.stdout)
            
            
            
            

class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Pyweaving GUI")
        
        # Sets the dimensions of the window
        screen_width = self.winfo_screenwidth() # Get the width of the screen
        screen_height = self.winfo_screenheight() # Get the height of the screen
        self.geometry("%dx%d+0+0" % (screen_width/2, min(600, screen_height*3/4)))
        #
        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=5, pady=5, sticky="nsew", columnspan=2) # colspan enables spreading out along with nsew
        
        # Feedback
        self.feedback = ctk.CTkTextbox(master=self)
        self.feedback.grid(row=1, column=0, padx=2, pady=2, sticky="nsew") # nsew enables expand_to_fill
        self.feedback.configure(wrap="none",border_width=2)
        self.rowconfigure(1, weight=1) # forces tabview to maintain size when resizing window
        self.columnconfigure(0, weight=1) # expands the tabview to fit
        self.tab_view.feedback = self.feedback
        
        
        # LOGO
        logo = ctk.CTkImage(light_image=Image.open("pyweaving-logo-100.png"),
                            dark_image=Image.open("pyweaving-logo-100.png"),
                            size=(84, 100))
        button_epl = ctk.CTkButton(self, text= '', image=logo, fg_color='transparent')
        button_epl.grid(row=1, column=1, padx=2, pady=2, sticky="se")
        button_epl.configure(state="disabled")
        
        #
        self.tab_view.set(tablabels["remap"])


app = App()
app.mainloop()