options = chr(0xF8B0)
play = chr(0xF5B0)
play_faded = chr(0xEE4A)
pause = chr(0xF8AE)
human_talk = chr(0xF8B2)
warning = chr(0xF736)
search = chr(0xF78B)
view_eye = chr(0xF78D)
folder = chr(0xF12B)
folder_open = chr(0xED25)
info = chr(0xF167)
spinner = chr(0xF16A)



if __name__ == "__main__":
    import customtkinter as ctk

    # Create the main window
    app = ctk.CTk()
    app.title("Font Icons Viewer")

    # Function to display icons in the scrollable frame
    def display_icons():
        # Clear existing icons
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get the start and end Unicode values from the entry widgets
        try:
            start_unicode = int(start_entry.get(), 16)  # Convert hex string to integer
            end_unicode = int(end_entry.get(), 16)    # Convert hex string to integer
        except ValueError:
            status_label.configure(text="Invalid Unicode range. Please enter valid hex values.")
            return
        
        # Validate the range
        if start_unicode > end_unicode:
            status_label.configure(text="Start Unicode must be less than or equal to End Unicode.")
            return
        
        # Display icons in the specified range
        for unicode_value in range(start_unicode, end_unicode + 1):
            try:
                # Convert Unicode value to a character
                icon_char = chr(unicode_value)
                
                # Create a frame for each icon
                icon_frame = ctk.CTkFrame(scrollable_frame)
                icon_frame.pack(fill="x", pady=2, padx=5)
                
                # Display the icon
                icon_label = ctk.CTkLabel(icon_frame, text=icon_char, font=icon_font, width=50)
                icon_label.pack(side="left", padx=10)
                
                # Display the Unicode value
                unicode_label = ctk.CTkLabel(icon_frame, text=f"U+{unicode_value:04X}")
                unicode_label.pack(side="left", padx=10)
            except Exception as e:
                print(f"Error displaying Unicode U+{unicode_value:04X}: {e}")
        
        # Update status label
        status_label.configure(text=f"Displaying icons from U+{start_unicode:04X} to U+{end_unicode:04X}")

    # Load the custom font (replace 'YourFontFile.ttf' with the path to your font file)
    icon_font = ctk.CTkFont(size=24)

    # Create a frame for the input fields and button
    input_frame = ctk.CTkFrame(app)
    input_frame.pack(pady=10, padx=20, fill="x")

    # Entry for start Unicode value
    start_label = ctk.CTkLabel(input_frame, text="Start Unicode (hex):")
    start_label.pack(side="left", padx=5)
    start_entry = ctk.CTkEntry(input_frame, width=100)
    start_entry.pack(side="left", padx=5)
    start_entry.insert(0, "E000")  # Default start value

    # Entry for end Unicode value
    end_label = ctk.CTkLabel(input_frame, text="End Unicode (hex):")
    end_label.pack(side="left", padx=5)
    end_entry = ctk.CTkEntry(input_frame, width=100)
    end_entry.pack(side="left", padx=5)
    end_entry.insert(0, "F8FF")  # Default end value

    # Regenerate button
    regenerate_button = ctk.CTkButton(input_frame, text="Regenerate", command=display_icons)
    regenerate_button.pack(side="left", padx=10)

    # Status label
    status_label = ctk.CTkLabel(app, text="Enter a Unicode range and click 'Regenerate'.")
    status_label.pack(pady=10)

    # Create a scrollable frame to hold the icons
    scrollable_frame = ctk.CTkScrollableFrame(app, width=400, height=300)
    scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

    # Run the application
    app.mainloop()