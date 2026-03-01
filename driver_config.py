import os
import json
import tkinter as tk
from tkinter import ttk, messagebox

CONFIG_FILE = "driver_config.json"

def load_config():
    """Load existing driver configuration if available"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    # Return default configuration if file doesn't exist or error occurs
    return {
        "name": "John Doe",
        "id": "DRV12345",
        "vehicle": "TN-01-AB-1234",
        "phone": "+1-555-123-4567"
    }

def save_config(config):
    """Save driver configuration to file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

class DriverConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Driver Credentials Configuration")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Load existing configuration
        self.config = load_config()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Driver Drowsiness Detection System", 
                               font=("Helvetica", 14, "bold"))
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(main_frame, text="Driver Credentials Configuration", 
                                 font=("Helvetica", 12))
        subtitle_label.pack(pady=5)
        
        # Driver info form
        form_frame = ttk.LabelFrame(main_frame, text="Driver Information", padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Driver Name
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        name_label = ttk.Label(name_frame, text="Driver Name:", width=15)
        name_label.pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=self.config["name"])
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=5)
        
        # Driver ID
        id_frame = ttk.Frame(form_frame)
        id_frame.pack(fill=tk.X, pady=5)
        id_label = ttk.Label(id_frame, text="Driver ID:", width=15)
        id_label.pack(side=tk.LEFT)
        self.id_var = tk.StringVar(value=self.config["id"])
        id_entry = ttk.Entry(id_frame, textvariable=self.id_var, width=30)
        id_entry.pack(side=tk.LEFT, padx=5)
        
        # Vehicle Number
        vehicle_frame = ttk.Frame(form_frame)
        vehicle_frame.pack(fill=tk.X, pady=5)
        vehicle_label = ttk.Label(vehicle_frame, text="Vehicle Number:", width=15)
        vehicle_label.pack(side=tk.LEFT)
        self.vehicle_var = tk.StringVar(value=self.config["vehicle"])
        vehicle_entry = ttk.Entry(vehicle_frame, textvariable=self.vehicle_var, width=30)
        vehicle_entry.pack(side=tk.LEFT, padx=5)
        
        # Phone Number
        phone_frame = ttk.Frame(form_frame)
        phone_frame.pack(fill=tk.X, pady=5)
        phone_label = ttk.Label(phone_frame, text="Phone Number:", width=15)
        phone_label.pack(side=tk.LEFT)
        self.phone_var = tk.StringVar(value=self.config["phone"])
        phone_entry = ttk.Entry(phone_frame, textvariable=self.phone_var, width=30)
        phone_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Save button
        save_button = ttk.Button(button_frame, text="Save Configuration", 
                              command=self.save_configuration)
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Run button
        run_button = ttk.Button(button_frame, text="Save & Run Detection", 
                             command=self.run_detection)
        run_button.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        reset_button = ttk.Button(button_frame, text="Reset to Default", 
                               command=self.reset_configuration)
        reset_button.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
    
    def save_configuration(self):
        """Save current configuration to file"""
        config = {
            "name": self.name_var.get(),
            "id": self.id_var.get(),
            "vehicle": self.vehicle_var.get(),
            "phone": self.phone_var.get()
        }
        
        # Basic validation
        if not all(config.values()):
            messagebox.showerror("Input Error", "All fields must be filled")
            return
            
        if save_config(config):
            self.config = config
            self.status_var.set("Configuration saved successfully!")
            messagebox.showinfo("Success", "Driver configuration has been saved successfully!")
        else:
            self.status_var.set("Error saving configuration")
            messagebox.showerror("Error", "Failed to save configuration")
    
    def reset_configuration(self):
        """Reset to default configuration"""
        default_config = {
            "name": "John Doe",
            "id": "DRV12345",
            "vehicle": "TN-01-AB-1234",
            "phone": "+1-555-123-4567"
        }
        
        self.name_var.set(default_config["name"])
        self.id_var.set(default_config["id"])
        self.vehicle_var.set(default_config["vehicle"])
        self.phone_var.set(default_config["phone"])
        
        self.status_var.set("Configuration reset to default values")
    
    def run_detection(self):
        """Save configuration and launch the detection system"""
        self.save_configuration()
        self.status_var.set("Starting drowsiness detection...")
        
        # Run the driver drowsiness detection system
        try:
            import subprocess
            subprocess.Popen(["python", "driver2.py"])
            self.root.destroy()  # Close the configuration window
        except Exception as e:
            self.status_var.set(f"Error launching detection: {e}")
            messagebox.showerror("Launch Error", f"Failed to start drowsiness detection: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DriverConfigApp(root)
    root.mainloop()