from fastapi import FastAPI, HTTPException, UploadFile, File, Body
import pandas as pd
import json
import os
import shutil
import uvicorn
import requests
from PyPDF2 import PdfReader
from googletrans import Translator
import numpy as np
from pydantic import BaseModel

app = FastAPI()

# مسیرهای ثابت
DATA_DIR = "/media/arshia/TEMP/data"
SYSTEM_DIR = "/media/arshia/TEMP/system"
KNOWLEDGE_DIR = "/media/arshia/TEMP/knowledge"
CONVERS_DIR = "/media/arshia/TEMP/conversation"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# -------------------- مدل Google Gemini --------------------
GEMINI_API_KEY = "AIzaSyDp5_hYaoSL2gW9L-UyhclBaBEtAI_4roo"  # توکن API معتبر خود را وارد کنید
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY

def query_gemini_model(user_message: str):
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [{"text": user_message}]
            }
        ]
    }
    
    response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    result = response.json()
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except KeyError:
        raise HTTPException(status_code=500, detail="Invalid response format from Gemini API")

# -------------------- صفحه انتخاب زبان --------------------
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/languages")
def get_languages():
    return {"languages": languages}

def calculate_ideal_weight(height_cm):
    height_m = height_cm / 100  # Convert height from cm to meters
    ideal_bmi = 22  # Standard BMI value (average for healthy individuals)
    ideal_weight = ideal_bmi * (height_m ** 2)  # Calculate ideal weight
    return ideal_weight

@app.post("/register")
def register_user(user_data: dict = Body(...)):
    required_fields = ["name", "height", "weight", "age", "gender", "exercise_hours", "country", "city", "username", "password", "email", "language"]
    
    if not all(field in user_data for field in required_fields):
        raise HTTPException(status_code=400, detail="All fields are required!")

    # چک کردن وجود کاربر
    file_path = os.path.join(DATA_DIR, f"{user_data['username']}.xlsx")
    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Username already exists!")

    bmi = user_data["weight"] / (user_data["height"] / 100) ** 2
    user_data["BMI"] = bmi


    user_weight = user_data['weight'] 
    user_height = user_data['height']

    # Calculate ideal weight
    ideal_weight = calculate_ideal_weight(user_height)

    # Calculate the weight difference (absolute value)
    weight_difference = abs(round(user_weight - ideal_weight, 2))  # Absolute value of weight difference

    # Determine the weight status based on the weight difference
    if user_weight > ideal_weight:
        weight_status = f"I have {weight_difference} kg of excess weight."
    elif user_weight < ideal_weight:
        weight_status = f"I have {weight_difference} kg of underweight."
    else:
        weight_status = "I have ideal weight."

    user_data["status"] = weight_status

    df = pd.DataFrame([user_data])
    df.to_excel(file_path, index=False)
    return {"message": "User registered successfully!"}



@app.post("/system")
def register_user(tone: dict = Body(...)):
    required_fields = ["tone","tone_prompt", "system_prompt", "creativity"]
    
    if not all(field in tone for field in required_fields):
        raise HTTPException(status_code=400, detail="All fields are required!")

    # مسیر ذخیره‌سازی فایل
    file_path = os.path.join(SYSTEM_DIR, f"{tone['tone']}.xlsx")

    # ایجاد فایل جدید در یک مسیر موقت
    temp_file_path = os.path.join(SYSTEM_DIR, f"temp_{tone['tone']}.xlsx")

    # ایجاد DataFrame و ذخیره در مسیر موقت
    df = pd.DataFrame([tone])
    df.to_excel(temp_file_path, index=False)

    # جایگزینی فایل جدید به جای فایل قبلی (در صورت وجود)
    os.replace(temp_file_path, file_path)

    return {"message": "File saved (replaced if existed) successfully!"}



@app.post("/login")
def login_user(user_data: dict = Body(...)):
    username = user_data.get("username")
    password = user_data.get("password")
    
    file_path = os.path.join(DATA_DIR, f"{username}.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="User not found!")
    
    df = pd.read_excel(file_path)
    stored_password = df.loc[0, "password"]
    if stored_password != password:
        raise HTTPException(status_code=400, detail="Invalid credentials!")
    
    return {"message": "Login successful!"}

@app.post("/rpga")
def summarize_all_pdfs():
    pdf_files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        raise HTTPException(status_code=404, detail="No PDF files found in the knowledge directory!")

    summaries = {}

    for pdf_file in pdf_files:
        file_path = os.path.join(KNOWLEDGE_DIR, pdf_file)
        attempts = 3  # تعداد تلاش‌ها برای خلاصه‌سازی
        for attempt in range(attempts):
            try:
                # خواندن متن PDF
                reader = PdfReader(file_path)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() + "\n"

                # خلاصه‌سازی متن PDF
                summary = query_gemini_model(pdf_text)
                summaries[pdf_file] = summary
                break  # اگر خلاصه‌سازی موفق بود، از حلقه خارج شوید

            except Exception as e:
                if attempt < attempts - 1:  # اگر هنوز تلاش بیشتری باقی مانده است
                    print(f"Attempt {attempt + 1} failed for {pdf_file}. Retrying...")
                else:
                    raise HTTPException(status_code=500, detail=f"Error summarizing {pdf_file}: {str(e)}")

    # ذخیره خلاصه‌ها در یک فایل JSON
    knowledge_json_path = os.path.join(DATA_DIR, "knowledge.json")
    with open(knowledge_json_path, "w", encoding="utf-8") as json_file:
        json.dump(summaries, json_file, ensure_ascii=False, indent=4)

    return {
        "message": "All PDFs summarized successfully!",
        "summaries_file": knowledge_json_path
    }


def translate_summary(summary: str, language_code: str) -> str:
    translator = Translator()
    translated = translator.translate(summary, dest=language_code).text
    return translated


translator = Translator()

tones=["friendly", "Sincerely", "seriously"]
import os
import json

import os
import json

@app.post("/user/chat")
def chat_with_model(chat_data: dict = Body(...)):
    username = chat_data.get("username")
    user_message = chat_data.get("user_message")
    selected_tone = chat_data.get("selected_tone")

    if not user_message or not username:
        raise HTTPException(status_code=400, detail="User message and username are required!")

    # مسیر فایل اکسل برای هر کاربر
    user_excel_path = os.path.join(DATA_DIR, f"{username}.xlsx")
    
    # چک کردن اینکه فایل اکسل وجود دارد یا نه
    if not os.path.exists(user_excel_path):
        raise HTTPException(status_code=400, detail="User's Excel file not found!")

    try:
        # بارگذاری فایل اکسل
        df = pd.read_excel(user_excel_path)
        weight_status = df['status'].iloc[-1]
        # پیدا کردن زبان کاربر از ستون "language"
        user_language = df['language'].iloc[0] 
        if user_language == "zh":
            user_language = "zh-cn"  # یا "zh-tw" بسته به نیاز
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading user's language from Excel: {str(e)}")

    # بارگذاری تنظیمات سیستم از فایل اکسل
    system_excel_path = os.path.join(SYSTEM_DIR, f"{selected_tone}.xlsx")

    if not os.path.exists(system_excel_path):
        raise HTTPException(status_code=400, detail="System settings file not found!")

    try:
        # بارگذاری تنظیمات سیستم از فایل Excel
        df = pd.read_excel(system_excel_path)

        # استخراج سیستم پرامپت و تو پرامپت
        system_prompt = df['system_prompt'].iloc[0]
        tone_prompt = df['tone_prompt'].iloc[0]
        
        # استخراج میزان خلاقیت از ستون "creativity"
        creativity_level = df['creativity'].iloc[0]  # میزان خلاقیت از ستون خوانده می‌شود

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading system settings: {str(e)}")

    # ترجمه پیام کاربر به انگلیسی
    try:
        user_message_in_english = translator.translate(user_message, src=user_language, dest="en").text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating user message to English: {str(e)}")

    # ترکیب پیام کاربر با سیستم پرامپت و تو پرامپت و میزان خلاقیت
    combined_message = f"{system_prompt}\n\nTone Prompt: {tone_prompt}\n\nUser Message:\n{user_message_in_english}\n\nUser Weight Status:\n{weight_status}\n\nCreativity Level: {creativity_level}"

    # بارگذاری مکالمات قبلی از فایل JSON
    conversation_file_path = os.path.join(CONVERS_DIR, f"{username}_conversation.json")

    # اگر فایل مکالمات کاربر وجود داشته باشد، آن را بارگذاری می‌کنیم
    if os.path.exists(conversation_file_path):
        with open(conversation_file_path, 'r') as file:
            conversation_data = json.load(file)
    else:
        conversation_data = {"conversations": []}

    # تاریخچه مکالمات را به پیام جدید اضافه می‌کنیم
    conversation_history = "\n".join([f"User: {conv['user_message']}\nModel: {conv['model_response']}" for conv in conversation_data["conversations"]])
    combined_message = f"{conversation_history}\n\n{combined_message}"

    # ارسال پیام به مدل و دریافت پاسخ به زبان انگلیسی
    try:
        model_response_in_english = query_gemini_model(combined_message)  # فرض بر این که این تابع مدل شماست
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Gemini model: {str(e)}")

    # بررسی اینکه آیا پاسخ مدل خالی یا None است
    if not model_response_in_english:
        raise HTTPException(status_code=500, detail="Model response is empty or None")

    # بررسی صحت پاسخ مدل و ترجمه آن
    if model_response_in_english:
        try:
            model_response_in_user_language = translator.translate(model_response_in_english, src="en", dest=user_language).text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error translating model response to user language: {str(e)}")
    else:
        model_response_in_user_language = "Sorry, I couldn't understand that."

    # ذخیره مکالمات جدید در فایل JSON
    conversation_data["conversations"].append({
        "user_message": user_message,
        "model_response": model_response_in_user_language
    })

    # ذخیره کردن مکالمه به فایل
    with open(conversation_file_path, 'w') as file:
        json.dump(conversation_data, file, indent=4)

    return {"response": model_response_in_user_language}



@app.get("/admin/users")
def get_user_data():
    user_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]
    user_data = []

    for file in user_files:
        try:
            df = pd.read_excel(os.path.join(DATA_DIR, file))
            username = os.path.splitext(file)[0]

            initial_weight = df.loc[0, "weight"] if "weight" in df.columns and not df["weight"].empty else None
            last_weight = df["weight"].iloc[-1] if "weight" in df.columns and not df["weight"].empty else initial_weight

            user_data.append({
                "username": username,
                "initial_weight": initial_weight.item() if isinstance(initial_weight, np.int64) else initial_weight,
                "last_weight": last_weight.item() if isinstance(last_weight, np.int64) else last_weight,
                "file_path": file
            })

        except Exception as e:
            print(f"Error processing file {file}: {str(e)}")

    return {"users": user_data}
@app.post("/admin/update_weight")
def update_user_weight(user_data: dict = Body(...)):
    username = user_data.get("username")
    password = user_data.get("password")
    new_weight = user_data.get("new_weight")

    user_file_path = os.path.join(DATA_DIR, f"{username}.xlsx")
    if not os.path.exists(user_file_path):
        raise HTTPException(status_code=404, detail="User not found!")

    # Load the user's Excel file
    df = pd.read_excel(user_file_path)
    
    # Verify password
    stored_password = df.loc[0, "password"] if "password" in df.columns else None
    if stored_password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials!")

    # If "weight" column doesn't exist, add it
    if "weight" not in df.columns:
        df["weight"] = pd.Series(dtype='float')

    # Calculate ideal weight and weight status for the new weight
    user_height = df['height'].iloc[0]  # Get the user's height from the first row
    ideal_weight = calculate_ideal_weight(user_height)  # Function to calculate ideal weight
    
    # Calculate the weight difference (absolute value)
    weight_difference = abs(round(new_weight - ideal_weight, 2))  # Absolute value of weight difference
    
    # Determine the weight status based on the weight difference
    if new_weight > ideal_weight:
        weight_status = f"I have {weight_difference} kg of excess weight."
    elif new_weight < ideal_weight:
        weight_status = f"I have {weight_difference} kg of underweight."
    else:
        weight_status = "I have ideal weight."
    
    # Create a new row with the new weight and status
    new_row = pd.DataFrame({"weight": [new_weight], "status": [weight_status]})
    
    # Append the new row to the existing DataFrame
    df = pd.concat([df, new_row], ignore_index=True)

    # Save the updated DataFrame to the Excel file
    df.to_excel(user_file_path, index=False)

    return {"message": "Weight and status updated successfully!"}


@app.post("/admin/add_pdf")
def add_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(KNOWLEDGE_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"File {file.filename} added successfully!"}

@app.delete("/admin/remove_pdf")
def remove_pdf(filename: str):
    file_path = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found!")
    os.remove(file_path)
    return {"message": f"File {filename} removed successfully!"}

@app.get("/admin/get_pdfs")
def list_pdfs():
    pdf_files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".pdf")]
    return {"pdf_files": pdf_files}

# -------------------- اجرای برنامه --------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)