import os
import time
import yaml
import tkinter as tk 
import tkinter.font as tk_font
from tkinter import (filedialog, messagebox, ttk)

from quiet_syntax import SyntaxHighlighter
from quiet_menubar import Menu, Menubar
from quiet_statusbar import Statusbar
from quiet_linenumbers import TextLineNumbers
from quiet_textarea import CustomText
from quiet_find import FindWindow


class QuietText(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        master.title('untitled - Quiet Text')
        # defined size of the editer window
        master.geometry('1920x1080')

        # defined editor basic bakground and looking
        master.tk_setPalette(background='#261e1b',
                             foreground='black',
                             activeForeground='white',
                             activeBackground='#9c8383',)

        # start editor according to defined settings in settings.yaml
        with open('config/settings.yaml') as settings_yaml:
            self.settings = yaml.load(settings_yaml, Loader=yaml.FullLoader)

        master.tk_setPalette(background='#272822', foreground='black')

        self.font_family = self.settings['font_family']
        self.bg_color = self.settings['bg_color']
        self.font_color = self.settings['font_color']
        self.tab_size = self.settings['tab_size']
        self.font_size = int(self.settings['font_size'])
        self.top_spacing = self.settings['top_spacing']
        self.bottom_spacing = self.settings['bottom_spacing']
        self.padding_x = self.settings['padding_x']
        self.padding_y = self.settings['padding_y']
        self.insertion_blink = 300 if self.settings['insertion_blink'] else 0
        self.insertion_color = self.settings['insertion_color']
        self.tab_size_spaces = self.settings['tab_size']
        self.text_wrap = self.settings['text_wrap']

        self.font_style = tk_font.Font(family=self.font_family,
                                       size=self.settings['font_size'])

        #configuration of the file dialog text colors.
        self.style = ttk.Style(master)
        self.style.configure('TLabel', foreground='black')
        self.style.configure('TEntry', foreground='black')
        self.style.configure('TMenubutton', foreground='black')
        self.style.configure('TButton', foreground='black')

        self.master = master
        self.filename = None
                                
        self.textarea = CustomText(self)

        self.scrolly = tk.Scrollbar(master,
                                    command=self.textarea.yview,
                                    bg='#383030',
                                    troughcolor='#2e2724',
                                    bd=0,
                                    width=8,
                                    highlightthickness=0,
                                    activebackground='#8a7575',
                                    orient='vertical')

        self.scrollx = tk.Scrollbar(master,
                                    command=self.textarea.xview,
                                    bg='#383030',
                                    troughcolor='#2e2724',
                                    bd=0,
                                    width=8,
                                    highlightthickness=0,
                                    activebackground='#8a7575',
                                    orient='horizontal')

        self.textarea.configure(yscrollcommand=self.scrolly.set,
                                xscrollcommand=self.scrollx.set,
                                bg=self.bg_color,
                                fg=self.font_color,
                                wrap= self.text_wrap,
                                spacing1=self.top_spacing, 
                                spacing3=self.bottom_spacing,
                                selectbackground='#75715e',
                                insertbackground=self.insertion_color,
                                insertofftime=self.insertion_blink,
                                bd=0,
                                highlightthickness=0,
                                font=self.font_family,
                                undo=True,
                                autoseparators=True,
                                maxundo=-1,
                                padx=self.padding_x,
                                pady=self.padding_y)

        #retrieving the font from the text area and setting a tab width
        self._font = tk_font.Font(font=self.textarea['font'])
        self._tab_width = self._font.measure(' ' * self.tab_size_spaces)
        self.textarea.config(tabs=(self._tab_width,))

        self.menubar = Menubar(self)
        self.statusbar = Statusbar(self)
        self.linenumbers = TextLineNumbers(self)
        self.syntax_highlighter = SyntaxHighlighter(self.textarea, 'languages/python.yaml')

        self.linenumbers.attach(self.textarea)
        self.scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollx.pack(side=tk.BOTTOM, fill='both')
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)
        self.textarea.pack(side=tk.RIGHT, fill='both', expand=True)

        # setting tk.RIGHT click menu bar
        self.right_click_menu = tk.Menu(master,
                                        font=self.font_family,
                                        fg='#d5c4a1',
                                        bg='#2e2724',
                                        activebackground='#9c8383',
                                        bd=0,
                                        tearoff=0)

        self.right_click_menu.add_command(label='Cut',
                                          accelerator='Ctrl+X',
                                          command=self.cut)

        self.right_click_menu.add_command(label='Copy',
                                          accelerator='Ctrl+C',
                                          command=self.copy)

        self.right_click_menu.add_command(label='Paste',
                                          accelerator='Ctrl+V',
                                          command=self.paste)
        self.right_click_menu.add_command(label='Bold',
                                          accelerator='Ctrl+B',
                                          command=self.bold)
        self.right_click_menu.add_command(label='Highlight',
                                          accelerator='Ctrl+G',
                                          command=self.hightlight)

        
        self.textarea.tag_configure('find_match', background='#75715e')
        self.textarea.find_match_index = None
        self.textarea.find_search_starting_index = 1.0
        #calling function to bind hotkeys.
        self.bind_shortcuts()
        self.control_key = False


    def load_settings_data(self, settings_path):
        settings_path = settings_path
        with open(settings_path, 'r') as settings_yaml:
            _settings = yaml.load(settings_yaml, Loader=yaml.FullLoader)
            return _settings

    def store_settings_data(self, information):
        with open('config/settings.yaml', 'w') as user_settings:
            yaml.dump(information, user_settings)

    def clear_and_replace_textarea(self):
            self.textarea.delete(1.0, tk.END)
            try:
                with open(self.filename, 'r') as f:
                    self.syntax_highlighter.on_key_release()
                    self.textarea.insert(1.0, f.read())
            except TypeError:
                pass

    #reconfigure the tab_width depending on changes.
    def set_new_tab_width(self, tab_spaces = 'default'):
        if tab_spaces == 'default':
            space_count = self.tab_size_spaces
        else:
            space_count = tab_spaces
        _font = tk_font.Font(font=self.textarea['font'])
        _tab_width = _font.measure(' ' * int(space_count))
        self.textarea.config(tabs=(_tab_width,))

    # editor basic settings can be altered here
    #function used to reload settings after the user changes in settings.yaml
    def reconfigure_settings(self, settings_path, overwrite=False):
            _settings = self.load_settings_data(settings_path)
            font_family = _settings['font_family']
            bg_color = _settings['bg_color']
            font_color = _settings['font_color']
            top_spacing = _settings['top_spacing']
            bottom_spacing = _settings['bottom_spacing']
            insertion_blink = 300 if _settings['insertion_blink'] else 0
            insertion_color = _settings['insertion_color']
            tab_size_spaces = _settings['tab_size']
            padding_x = _settings['padding_x']
            padding_y = _settings['padding_y']
            text_wrap = _settings['text_wrap']

            font_style = tk_font.Font(family=font_family,
                                      size=_settings['font_size'])

            self.textarea.configure(font=font_style,
                                    bg=bg_color,
                                    pady=padding_y,
                                    padx=padding_x,
                                    fg=font_color,
                                    spacing1=top_spacing,
                                    spacing3=bottom_spacing,
                                    insertbackground=insertion_color,
                                    insertofftime=insertion_blink,
                                    wrap=text_wrap)

            self.set_new_tab_width(tab_size_spaces)

            if overwrite:
                MsgBox = tk.messagebox.askquestion('Reset Settings?',
                                                   'Are you sure you want to reset the editor settings to their default value?',
                                                    icon='warning')
                if MsgBox == 'yes':
                    self.store_settings_data(_settings)
                else:
                    self.save('config/settings.yaml')

    # editor quiet mode calling which removes status bar and menu bar
    def enter_quiet_mode(self, *args):
        self.statusbar.hide_status_bar()
        self.menubar.hide_menu()
        self.scrollx.configure(width=0)
        self.scrolly.configure(width=0)
        self.statusbar.update_status('quiet')

    # editor leaving quite enu to bring back status bar and menu bar
    def leave_quiet_mode(self, *args):
        self.statusbar.show_status_bar()
        self.menubar.show_menu()
        self.scrollx.configure(width=8)
        self.scrolly.configure(width=8)
        self.statusbar.update_status('hide')

    #hide status bar for text class so it can be used in menu class
    def hide_status_bar(self, *args):
        self.statusbar.hide_status_bar()

    # setting up the editor title
    #Renames the window title bar to the name of the current file.
    def set_window_title(self, name=None):
        if name:
            self.master.title(f'{name} - QuietText')
        else:
            self.master.title('Untitled - QuietText')

    # new file creating in the editor feature
    #Deletes all of the text in the current area and sets window title to default.
    def new_file(self, *args):
        self.textarea.delete(1.0, tk.END)
        self.filename = None
        self.set_window_title()

    # opening an existing file in the editor
    def open_file(self, *args):
        # various file types that editor can support
        self.filename = filedialog.askopenfilename(
            defaultextension='.txt',
            filetypes=[('All Files', '*.*'),
                       ('Text Files', '*.txt'),
                       ('Python Scripts', '*.py'),
                       ('Markdown Documents', '*.md'),
                       ('Javascript Files', '*.js'),
                       ('HTML Documents', '*.html'),
                       ('CSS Documents', '*.css')])

        if self.filename:
            self.clear_and_replace_textarea()
            self.set_window_title(name=self.filename)
            if self.filename[-3:] == '.py':
                self.syntax_highlighter.on_key_release()

    # saving changes made in the file
    def save(self,*args):
        if self.filename:
            try:
                textarea_content = self.textarea.get(1.0, tk.END)
                with open(self.filename, 'w') as f:
                    f.write(textarea_content)
                self.statusbar.update_status('saved')
                if self.filename == 'config/settings.yaml':
                    self.reconfigure_settings(self.filename)
                    self.menubar.reconfigure_settings()
            except Exception as e:
                print(e)
        else:
            self.save_as()

    # saving file as a particular name
    def save_as(self, *args):
        try:
            new_file = filedialog.asksaveasfilename(
                initialfile='untitled.txt',
                defaultextension='.txt',
                filetypes=[('All Files', '*.*'),
                           ('Text Files', '*.txt'),
                           ('Python Scripts', '*.py'),
                           ('Markdown Documents', '*.md'),
                           ('Javascript Files', '*.js'),
                           ('HTML Documents', '*.js'),
                           ('CSS Documents', '*.css')])

            textarea_content = self.textarea.get(1.0, tk.END)
            with open(new_file, 'w') as f:
                f.write(textarea_content)
            self.filename = new_file
            self.set_window_title(self.filename)
            self.statusbar.update_status('saved')
        except Exception as e:
            print(e)
            
    #On exiting the Program
    def quit_save(self):
        try:
            os.path.isfile(self.filename)
            self.save()          
            
        except:
            self.save_as()
        quit()
                        

    def on_closing(self):
        message = tk.messagebox.askyesnocancel("Save On Close", "Do you want to save the changes before closing?")
        if message == True:
            self.quit_save()
        elif message == False:
            quit()
        else:
            return

    # running the python file
    def run(self, *args):
        try:
            if self.filename[-3:] == '.py':
                #run separate commands for different os
                if os.name == 'nt':
                    os.system(f'start cmd.exe @cmd /k "python {self.filename}"')
                else:
                    os.system(f"gnome-terminal -- python3.8 {self.filename}")
            else:
                self.statusbar.update_status('no python')
        except TypeError:
            self.statusbar.update_status('no file run')

    # opens the main setting file of the editor
    def open_settings_file(self):
        self.filename = 'config/settings.yaml'
        self.textarea.delete(1.0, tk.END)
        with open(self.filename, 'r') as f:
            self.textarea.insert(1.0, f.read())
        self.set_window_title(name=self.filename)
        self.syntax_highlighter.on_key_release()

    # reset the settings set by the user to the default settings
    def reset_settings_file(self):
        self.reconfigure_settings('config/settings-default.yaml', overwrite=True)
        self.clear_and_replace_textarea()
        self.syntax_highlighter.on_key_release()

    # select all written text in the editor
    def select_all_text(self, *args):
        self.textarea.tag_add(tk.SEL, '1.0', tk.END)
        self.textarea.mark_set(tk.INSERT, '1.0')
        self.textarea.see(tk.INSERT)
        return 'break'

    # give hex colors to the file content for better understanding
    def apply_hex_color(self, key_event):
        new_color = self.menubar.open_color_picker()
        try:
            sel_start = self.textarea.index(tk.SEL_FIRST)
            sel_end = self.textarea.index(tk.SEL_LAST)
            self.textarea.delete(sel_start, sel_end)
            self.textarea.insert(sel_start, new_color)
        except tk.TclError:
            pass

    # Render the tk.RIGHT click menu on tk.RIGHT click
    def show_click_menu(self, key_event):
        self.right_click_menu.tk_popup(key_event.x_root, key_event.y_root)

    # shortcut keys that the editor supports
    def copy(self, event=None):
        try:
            self.textarea.clipboard_clear()
            text=self.textarea.get("sel.first", "sel.last")
            self.textarea.clipboard_append(text)
        except tk.TclError:
            pass

    def cut(self,event=None):
        try:
            self.copy()
            self.textarea.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

    def paste(self, event=None):
        try:
            text = self.textarea.selection_get(selection='CLIPBOARD')
            self.textarea.insert('insert',text)
        except tk.TclError:
            pass

    # Setting the selected text to be bold
    def bold(self, event=None):
        if self.filename:
            try:
                if(os.path.splitext(self.filename)[1][1:] == "txt"):
                    current_tags = self.textarea.tag_names("sel.first")
                    bold_font = tk_font.Font(self.textarea, self.textarea.cget("font"))
                    bold_font.configure(weight = "bold")
                    self.textarea.tag_config("bold", font = bold_font)
                    if "bold" in current_tags:
                        self.textarea.tag_remove("bold", "sel.first", "sel.last")
                    else:
                        self.textarea.tag_add("bold", "sel.first", "sel.last")
                else: 
                    self.statusbar.update_status('no txt bold')
            except tk.TclError:
                pass
        else:
            self.statusbar.update_status('no file')

    def hightlight(self, event=None):
        if self.filename:
            try:
                if(os.path.splitext(self.filename)[1][1:] == "txt"):
                    new_color = self.menubar.open_color_picker()
                    current_tags = self.textarea.tag_names("sel.first")
                    highlight_font = tk_font.Font(self.textarea, self.textarea.cget("font"))
                    self.textarea.tag_config("highlight", font = highlight_font, foreground = "black", background = new_color)
                    if "highlight" in current_tags:
                        self.textarea.tag_remove("highlight", "sel.first", "sel.last")
                    else:
                        self.textarea.tag_add("highlight", "sel.first", "sel.last")
                else:
                    self.statusbar.update_status('no txt high')
            except tk.TclError:
                pass
        else:
            self.statusbar.update_status('no file')
            
          
    def _on_change(self, key_event):
        self.linenumbers.redraw()

    def _on_mousewheel(self, event):
        if self.control_key:
            self.change_font_size(1 if event.delta > 0 else -1)

    def _on_linux_scroll_up(self, _):
        if self.control_key:
            self.change_font_size(1)
            if self.filename == 'config/settings.yaml':
                self.syntax_highlighter.on_key_release()

    def _on_linux_scroll_down(self, _):
        if self.control_key:
            self.change_font_size(-1)
            if self.filename == 'config/settings.yaml':
                self.syntax_highlighter.on_key_release()

    def change_font_size(self, delta):
        self.font_size = self.font_size + delta
        min_font_size = 6
        self.font_size = min_font_size if self.font_size < min_font_size else self.font_size
        self.font_style = tk_font.Font(family=self.font_family,
                                       size=self.font_size)

        self.textarea.configure(font=self.font_style)
        self.set_new_tab_width()
        _settings = self.load_settings_data('config/settings.yaml')
        _settings['font_size'] = self.font_size
        self.store_settings_data(_settings)

        if self.filename == 'config/settings.yaml':
            self.clear_and_replace_textarea()


    # control_l = 37
    # control_r = 109
    # mac_control = 262401 #control key in mac keyboard
    # mac_control_l = 270336 #tk.LEFT control key in mac os with normal keyboard
    # mac_control_r = 262145 #tk.RIGHT control key in mac os with normal keyboard
    def _on_keydown(self, event):
        if event.keycode in [37, 109, 262401, 270336, 262145]:
            self.control_key = True
            self.textarea.isControlPressed = True
        else:
            self.statusbar.update_status('hide')

    # def _on_keyup(self, event):
    #     if event.keycode in [37, 109, 262401, 270336, 262145]:
    #         self.control_key = False
    #         self.textarea.isControlPressed = False
    # self.textarea.bind('<KeyRelease>', self._on_keyup)

    def syntax_highlight(self, event):
        if self.filename and self.filename[-3:] == '.py':
            self.syntax_highlighter.on_key_release()

        self.control_key = False
        self.textarea.isControlPressed = False

    def show_find_window(self, event=None):
        FindWindow(self.textarea)
        self.control_key = False
        self.textarea.isControlPressed = False

    def bind_shortcuts(self, *args):
        self.textarea.bind('<Control-n>', self.new_file)
        self.textarea.bind('<Control-o>', self.open_file)
        self.textarea.bind('<Control-s>', self.save)
        self.textarea.bind('<Control-S>', self.save_as)
        self.textarea.bind('<Control-b>', self.bold)
        self.textarea.bind('<Control-h>', self.hightlight)
        self.textarea.bind('<Control-a>', self.select_all_text)
        self.textarea.bind('<Control-m>', self.apply_hex_color)
        self.textarea.bind('<Control-r>', self.run)
        self.textarea.bind('<Control-q>', self.enter_quiet_mode)
        self.textarea.bind('<Control-f>', self.show_find_window)
        self.textarea.bind('<Escape>', self.leave_quiet_mode)
        self.textarea.bind('<<Change>>', self._on_change)
        self.textarea.bind('<Configure>', self._on_change)
        self.textarea.bind('<Button-3>', self.show_click_menu)
        self.textarea.bind('<MouseWheel>', self._on_mousewheel)
        self.textarea.bind('<Button-4>', self._on_linux_scroll_up)
        self.textarea.bind('<Button-5>', self._on_linux_scroll_down)
        self.textarea.bind('<Key>', self._on_keydown)
        self.textarea.bind('<KeyRelease>', self.syntax_highlight)


if __name__ == '__main__':
    master = tk.Tk()
    try:
        p1 = tk.PhotoImage(file='../images/q.png')
        master.iconphoto(False, p1)
    except Exception as e:
        print(e)
    qt = QuietText(master)
    qt.pack(side='top', fill='both', expand=True)
    master.protocol("WM_DELETE_WINDOW", qt.on_closing)
    master.mainloop()











