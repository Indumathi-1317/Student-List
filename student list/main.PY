import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import mysql.connector
import os
import shutil
import webbrowser
from datetime import datetime

DOWNLOAD_FOLDER = r"D:\Users\Indumathi\file_details"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

department_mapping = {
    "1": "AI",
    "2": "IT",
    "3": "ECE",
    "4": "EEE",
    "5": "CSE"
}

def save_data():
    name = name_textbox.get()
    dob = age_textbox.get()
    department = department_textbox.get()
    mobile = mobile_textbox.get()
    email = email_textbox.get()
    password = password_textbox.get()

    if not name or not email or not password:
        messagebox.showerror("Input Error", "Name, Email, and Password are required fields!")
        return

    if department not in department_mapping:
        messagebox.showerror("Input Error", "Please enter a valid department number (1-5).")
        return

    try:
        dob_date = datetime.strptime(dob, '%Y-%m-%d')
        age = (datetime.now() - dob_date).days // 365
    except ValueError:
        messagebox.showerror("File Error", "Please enter a valid date of birth (yyyy-mm-dd).")
        return
    age_label.config(text=f"Age: {age}")

    image_path = image_path_textbox.get()
    pdf_path = pdf_path_textbox.get()
    text_path = text_path_textbox.get()

    def check_file_size(file_path, max_size_mb):
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > max_size_mb:
            return False, file_size
        return True, file_size

    is_valid_image, image_size = check_file_size(image_path, 5)
    if not is_valid_image:
        messagebox.showerror("File Size Error", f"Image file size is too large! ({image_size:.2f} MB)")
        return

    is_valid_pdf, pdf_size = check_file_size(pdf_path, 10)
    if not is_valid_pdf:
        messagebox.showerror("File Size Error", f"PDF file size is too large! ({pdf_size:.2f} MB)")
        return

    is_valid_text, text_size = check_file_size(text_path, 1)
    if not is_valid_text:
        messagebox.showerror("File Size Error", f"Text file size is too large! ({text_size:.2f} MB)")
        return

    image_name = os.path.basename(image_path)
    pdf_name = os.path.basename(pdf_path)
    text_name = os.path.basename(text_path)

    image_dest = os.path.join(DOWNLOAD_FOLDER, image_name)
    pdf_dest = os.path.join(DOWNLOAD_FOLDER, pdf_name)
    text_dest = os.path.join(DOWNLOAD_FOLDER, text_name)

    try:
        shutil.copy(image_path, image_dest)
        shutil.copy(pdf_path, pdf_dest)
        shutil.copy(text_path, text_dest)
    except Exception as e:
        messagebox.showerror("File Error", f"Error copying files: {e}")
        return

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="form"
        )
        cursor = conn.cursor()

        create_file_table_query = """
        CREATE TABLE IF NOT EXISTS file_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            image_name VARCHAR(255),
            pdf_name VARCHAR(255),
            text_name VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES user_details(id)
        )
        """
        cursor.execute(create_file_table_query)

        query = "INSERT INTO user_details (name, age, department, mobile, email, password) VALUES (%s, %s, %s, %s, %s, %s)"
        data = (name, age, department, mobile, email, password)
        cursor.execute(query, data)
        user_id = cursor.lastrowid

        file_query = "INSERT INTO file_details (user_id, image_name, pdf_name, text_name) VALUES (%s, %s, %s, %s)"
        cursor.execute(file_query, (user_id, image_name, pdf_name, text_name))

        conn.commit()

        cursor.close()
        conn.close()

        messagebox.showinfo("Success", "Data saved successfully!")

        name_textbox.delete(0, tk.END)
        age_textbox.delete(0, tk.END)
        department_textbox.delete(0, tk.END)
        mobile_textbox.delete(0, tk.END)
        email_textbox.delete(0, tk.END)
        password_textbox.delete(0, tk.END)
        image_path_textbox.delete(0, tk.END)
        pdf_path_textbox.delete(0, tk.END)
        text_path_textbox.delete(0, tk.END)

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def show_data():
    new_window = tk.Toplevel(root)
    new_window.title("List of Users")

    treeview = ttk.Treeview(new_window, columns=("Name", "Age", "Mobile", "Email", "Profile", "Resume", "Text"), show="headings")
    treeview.pack(fill="both", expand=True)

    treeview.heading("Name", text="Name")
    treeview.heading("Age", text="Age")
    treeview.heading("Mobile", text="Mobile")
    treeview.heading("Email", text="Email")
    treeview.heading("Profile", text="Profile")
    treeview.heading("Resume", text="Resume")
    treeview.heading("Text", text="Text")

    def open_file(file_path):
        """Open the file with the webbrowser."""
        try:
            webbrowser.open(f"file://{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="form"
        )
        cursor = conn.cursor()

        query = """
            SELECT u.name, u.age, u.mobile, u.email, f.image_name, f.pdf_name, f.text_name
            FROM user_details u
            JOIN file_details f ON u.user_id = f.user_id
        """
        cursor.execute(query)
        
        rows = cursor.fetchall()

        for row in rows:
            name, age, mobile, email, image_name, pdf_name, text_name = row
            image_link = os.path.join(DOWNLOAD_FOLDER, image_name)
            pdf_link = os.path.join(DOWNLOAD_FOLDER, pdf_name)
            text_link = os.path.join(DOWNLOAD_FOLDER, text_name)
            print(image_link)
            treeview.insert("", "end", values=(
                name, age, mobile, email,
                f"Profile: {image_name}",
                f"Resume: {pdf_name}",
                f"Text: {text_name}"
            ))

            treeview.bind(image_name,"<Button-1>", lambda e, path=image_link: open_file(path))
            treeview.bind(pdf_name,"<Button-1>", lambda e, path=pdf_link: open_file(path))
            treeview.bind(text_name,"<Button-1>", lambda e, path=text_link: open_file(path))
            

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")



def browse_image():
    filename = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if filename:
        image_path_textbox.delete(0, tk.END)
        image_path_textbox.insert(0, filename)

def browse_pdf():
    filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if filename:
        pdf_path_textbox.delete(0, tk.END)
        pdf_path_textbox.insert(0, filename)

def browse_text():
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filename:
        text_path_textbox.delete(0, tk.END)
        text_path_textbox.insert(0, filename)

root = tk.Tk()
root.title("Student Registration Form")

name_label = tk.Label(root, text="Enter Name")
name_label.pack()
name_textbox = tk.Entry(root)
name_textbox.pack()

age_label = tk.Label(root, text="Enter DOB (YYYY-MM-DD)")
age_label.pack()
age_textbox = tk.Entry(root)
age_textbox.pack()

department_label = tk.Label(root, text="Enter Department (1: AI, 2: IT, 3: ECE, 4: EEE, 5: CSE)")
department_label.pack()
department_textbox = tk.Entry(root)
department_textbox.pack()

mobile_label = tk.Label(root, text="Enter Mobile No")
mobile_label.pack()
mobile_textbox = tk.Entry(root)
mobile_textbox.pack()

email_label = tk.Label(root, text="Enter Email")
email_label.pack()
email_textbox = tk.Entry(root)
email_textbox.pack()

password_label = tk.Label(root, text="Enter Password")
password_label.pack()
password_textbox = tk.Entry(root, show="*")
password_textbox.pack()

image_label = tk.Label(root, text="Select Image")
image_label.pack()
image_path_textbox = tk.Entry(root)
image_path_textbox.pack()
image_button = tk.Button(root, text="Browse Image", command=browse_image)
image_button.pack()

pdf_label = tk.Label(root, text="Select PDF")
pdf_label.pack()
pdf_path_textbox = tk.Entry(root)
pdf_path_textbox.pack()
pdf_button = tk.Button(root, text="Browse PDF", command=browse_pdf)
pdf_button.pack()

text_label = tk.Label(root, text="Select Text File")
text_label.pack()
text_path_textbox = tk.Entry(root)
text_path_textbox.pack()
text_button = tk.Button(root, text="Browse Text", command=browse_text)
text_button.pack()

submit_button = tk.Button(root, text="Submit", command=save_data)
submit_button.pack()

show_button = tk.Button(root, text="Show List", command=show_data)
show_button.pack(pady=20)

root.mainloop()