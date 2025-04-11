import requests
import os
import json

API_BASE_URL = "http://127.0.0.1:8000"

languages = [
    {"code": "en", "name": "English"},
    {"code": "fa", "name": "Persian"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "zh-cn", "name": "Chinese"}, 
    {"code": "ru", "name": "Russian"},
    {"code": "ar", "name": "Arabic"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "it", "name": "Italian"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "hi", "name": "Hindi"},
    {"code": "tr", "name": "Turkish"},
    {"code": "nl", "name": "Dutch"},
    {"code": "pl", "name": "Polish"},
    {"code": "sv", "name": "Swedish"},
    {"code": "no", "name": "Norwegian"},
    {"code": "da", "name": "Danish"},
    {"code": "fi", "name": "Finnish"}
]

def register_user():
    # دریافت اطلاعات کاربر از ورودی
    name = input("Enter your name: ")
    height = float(input("Enter your height (in cm): "))
    weight = float(input("Enter your weight (in kg): "))
    age = int(input("Enter your age: "))
    gender = input("Enter your gender (male/female): ")
    exercise_hours = float(input("Enter hours of exercise per week: "))
    country = input("Enter your country: ")
    city = input("Enter your city: ")
    username = input("Enter username: ")
    password = input("Enter password: ")
    email = input("Enter your email: ")

    # نمایش زبان‌ها و دریافت زبان انتخابی
    print("Available languages:")
    for idx, lang in enumerate(languages):
        print(f"{idx + 1}. {lang['name']} (Code: {lang['code']})")
    
    language_choice = int(input("Choose a language by number: "))
    chosen_language = languages[language_choice - 1]['code']  # انتخاب زبان بر اساس شماره

    # محاسبه BMI
    bmi = weight / (height / 100) ** 2

    # ارسال درخواست ثبت‌نام به API
    response = requests.post(f"{API_BASE_URL}/register", json={
        "name": name,
        "height": height,
        "weight": weight,
        "age": age,
        "gender": gender,
        "exercise_hours": exercise_hours,
        "country": country,
        "city": city,
        "username": username,
        "password": password,
        "email": email,
        "BMI": bmi,
        "language": chosen_language  # اضافه کردن زبان انتخابی به درخواست
    })
    print(response.json())

tones=["friendly", "Sincerely", "seriously"]

def system_setting():
    # دریافت اطلاعات کاربر از ورودی
    print("Available System Tones :")
    for idx, lang in enumerate(tones):
            print(f"{idx + 1}. {lang}")
    tone = int(input("Choose System Tone : "))
    chosen_tone = tones[tone - 1]

    tone_prompt = input("Enter Tone prompt : ")
  
    system_prompt = input("Enter System prompt : ")

    while True:
        try:
            creativity = int(input("Choose a number between 1 and 10 (Lower = More Accuracy, Higher = More Creativity): "))

            if 1 <= creativity <= 10:
                break  # Valid input, exit the loop
            else:
                print("Please enter a number between 1 and 10.")

        except ValueError:
            print("Invalid input! Please enter a number between 1 and 10.")

    # Display the appropriate message based on the selected number
    if creativity <= 5:
        print(f"You chose {creativity}. The model will be more accurate.")
    else:
        print(f"You chose {creativity}. The model will be more creative.")


    # ارسال درخواست ثبت‌نام به API
    response = requests.post(f"{API_BASE_URL}/system", json={
        "tone": chosen_tone,
        "tone_prompt": tone_prompt,
        "system_prompt": system_prompt,
        "creativity": creativity,
    })
    print(response.json())


def login_user():
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    response = requests.post(f"{API_BASE_URL}/login", json={
        "username": username,
        "password": password
    })

    try:
        response.raise_for_status()
        data = response.json()
        print(data)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except ValueError:
        print("Response content is not valid JSON")

def save_chat_memory(username, message):
    file_path = f"{username}_chat_memory.json"
    chat_memory = {"messages": []}  # Initialize with empty messages list

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            chat_memory = json.load(f)

    chat_memory['messages'].append(message)

    with open(file_path, 'w') as f:
        json.dump(chat_memory, f)

def load_chat_memory(username):
    file_path = f"{username}_chat_memory.json"
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def chat_with_model():
    username = input("Enter username: ")
    user_message = input("Enter your message: ")

    # نمایش گزینه‌های لحن برای کاربر
    print("Available System Tones:")
    for idx, tone in enumerate(tones):
        print(f"{idx + 1}. {tone}")

    try:
        tone_choice = int(input("Choose System Tone: ")) - 1
        if tone_choice < 0 or tone_choice >= len(tones):
            print("Invalid tone choice!")
            return
        selected_tone = tones[tone_choice]
    except ValueError:
        print("Invalid input for tone choice!")
        return

    # ارسال داده‌ها به API
    response = requests.post(f"{API_BASE_URL}/user/chat", json={
        "username": username,
        "user_message": user_message,
        "selected_tone": selected_tone  # ارسال انتخاب لحن
    })

    # نمایش پاسخ API
    if response.status_code == 200:
        print("Model Response: ", response.json()['response'])
    else:
        print(f"Error: {response.status_code}, {response.text}")


def list_users():
    response = requests.get(f"{API_BASE_URL}/admin/users")
    print(response.json())

def add_pdf():
    filename = input("Enter PDF filename to upload: ")
    with open(filename, 'rb') as f:
        response = requests.post(f"{API_BASE_URL}/admin/add_pdf", files={"file": f})
    print(response.json())

def remove_pdf():
    filename = input("Enter PDF filename to remove: ")
    response = requests.delete(f"{API_BASE_URL}/admin/remove_pdf", json={"filename": filename})
    print(response.json())



def get_languages():
    response = requests.get(f"{API_BASE_URL}/languages")
    print(response.json())

def summarize_pdfs():
    response = requests.post(f"{API_BASE_URL}/rpga")
    print(response.json())

def update_user_weight():
    username = input("Enter username: ")
    password = input("Enter password: ")
    new_weight = float(input("Enter new weight (in kg): "))

    response = requests.post(f"{API_BASE_URL}/admin/update_weight", json={
        "username": username,
        "password": password,
        "new_weight": new_weight
    })

    if response.ok:
        print("Weight updated successfully!")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")

def main():
    while True:
        print("\nOptions:")
        print("1. Register User")
        print("2. Login User")
        print("3. Model Setting")
        print("4. Chat with Model")
        print("5. List Users")
        print("6. Add PDF")
        print("7. Remove PDF")
        print("8. Summarize PDFs")
        print("9. Update User Weight")  # اضافه کردن گزینه ویرایش وزن
        print("10. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == '1':
            register_user()
        elif choice == '2':
            login_user()
        elif choice == '3':
            system_setting()
        elif choice == '4':
            chat_with_model()
        elif choice == '5':
            list_users()
        elif choice == '6':
            add_pdf()
        elif choice == '7':
            remove_pdf()
        elif choice == '8':
            summarize_pdfs()
        elif choice == '9':
            update_user_weight()  # فراخوانی تابع ویرایش وزن
        elif choice == '10':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()