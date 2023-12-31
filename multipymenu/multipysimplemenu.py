from dataclasses import dataclass, field
import os
import re
from typing import Optional
from .multipyterminal import print_lines, delete_lines, delete_all_lines, cursor_backwards, is_decodable, clear_terminal, MultiPyKeyStrokes
from .multipycolors import MultiPyColors, MultiPyStyles, ENDC
from .multipymath import clamp
from .special_keys import SpecialKeys

@dataclass
class MultiPySimpleMenu:
    """ Simple CLI menu for windows

    Args:
        options (list[str]): List of the options for the menu
        default_option (int): Deafult option that will be highlihged
        prechar (str): Prechar for the options. Defaults to "> "
        clear_on_exit (bool): Clear console in exit of the menu. Defaults on True
        selected_color (MultiPyColors): Color of the selected option. Defaults to None
        selected_style (MultiPyStyles): Font style pf the seletect option. Defaults to None
    
    """
    options:list[str]
    default_option:int = 0
    prechar:str = "> "
    clear_on_exit:bool = True
    selected_color:MultiPyColors = MultiPyColors.NONE
    selected_style:MultiPyStyles = MultiPyStyles.UNDERLINE
    
    _selected_option:int = default_option
    _searching_buffer:str = ""

    # Size in lines of the terminal
    _terminal_last_line_size:int = os.get_terminal_size().lines

    # Size in columns of the terminal
    _terminal_last_column_size:int = os.get_terminal_size().columns

    
    @property
    def _printable_options(self):
        """"Return the formatted options to print"""
        temp_option:str
        temp_printable_options:list = []

        available_options:list[str] = []

         # Checks if searching is active, that is to say, user has typed at least /
        if self._searching:
            # Filter options based on search pattern
            for option in self.options:
                if re.match(re.escape(self._searching_buffer[1:]), option):
                    available_options.append(option)
        else:
            available_options = self.options[:]

        # Adds the styles selected to the options
        for index, option in enumerate(available_options):
            temp_option = option
            if index == self._selected_option:
                temp_option = self.selected_color.value + self.selected_style.value + temp_option
            temp_option = self.prechar + temp_option + ENDC
            temp_printable_options.append(temp_option)
        return temp_printable_options
    
    @property
    def _terminal_resized(self) -> bool:
        """Check if the terminal has been resized"""
        return os.get_terminal_size().lines != self._terminal_last_line_size or os.get_terminal_size().columns != self._terminal_last_column_size

    @property
    def _searching(self) -> bool:
        """Check if searching is active by checking the length of the searching buffer"""
        return len(self._searching_buffer) > 0

    def show(self) -> Optional[int]:
        """ Displays the menu and handles user interactions.

            This method clears the terminal and prints the menu options. It continuously listens for keyboard input from the user.
            The menu supports arrow key navigation, search functionality, and the Enter key to select an option.

            Returns:
                int: The index of the selected option.
                clear_terminal()
                print_lines(self._printable_options, self._searching_buffer)
        """

        kshandler = MultiPyKeyStrokes()
        kshandler.init()

        print_lines(self._printable_options, self._searching_buffer)

        try:
            while True:
                # Checks if the terminal has been resized
                if self._terminal_resized:
                    self._terminal_last_line_size = os.get_terminal_size().lines
                    self._terminal_last_column_size = os.get_terminal_size().columns
                    clear_terminal()
                    print_lines(self._printable_options, self._searching_buffer)

                # Checks for a key stroke
                key = kshandler.readch()
                    
                if key == SpecialKeys.INTRO:
                    if self.clear_on_exit:
                        # Delete all lines including the searching buffer
                        delete_all_lines(self._searching_buffer, self._terminal_last_line_size)
                    else:
                        # Delete lines below the menu options
                        delete_lines(lines=os.get_terminal_size().lines - len(self.options)-1)
                    kshandler.deinit()
                    if len(self._printable_options) != 0:
                        return self._selected_option
                    return None
                
                elif key == SpecialKeys.ARROW_UP:
                    self._selected_option -= 1
                elif key == SpecialKeys.ARROW_DOWN:
                    self._selected_option += 1
                elif key == SpecialKeys.SLASH and not self._searching:
                    self._searching_buffer = "/"
                elif self._searching:
                    if key == SpecialKeys.BACKSPACE:
                        char_to_remove = self._searching_buffer[-1]
                        self._searching_buffer = self._searching_buffer[:-1]
                        # In case character to be deleted is a TAB
                        cursor_backwards(times=7) if char_to_remove.encode() == b'\t' else cursor_backwards()
                    elif isinstance(key, str):
                        self._searching_buffer += key

                self._selected_option = clamp(self._selected_option, 0, len(self._printable_options)-1)
                        
                delete_all_lines(self._searching_buffer, self._terminal_last_line_size)
                print_lines(self._printable_options, self._searching_buffer)
        finally:
            kshandler.deinit()
