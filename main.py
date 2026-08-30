import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import fitz  # مكتبة PyMuPDF المتوافقة مع السحابة
import img2pdf
from docx import Document
from flask import Flask
from threading import Thread

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- إعداد خادم ويب وهمي لإبقاء البوت يعمل 24/7 على منصة Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running perfectly 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# ---------------------------------------------------------------

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("الرجاء إرسال ملف صالح.")
        return

    doc = update.message.document
    file_name = doc.file_name
    file_extension = file_name.split('.')[-1].lower()
    
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", file_name)
    
    new_file = await context.bot.get_file(doc.file_id)
    await new_file.download_to_drive(file_path)
    
    await update.message.reply_text("⏳ جاري معالجة وتحويل الملف، انتظر لحظات...")

    try:
        if file_extension == 'pdf':
            # تحويل PDF إلى صور باستخدام PyMuPDF
            pdf_doc = fitz.open(file_path)
            for page in pdf_doc:
                pix = page.get_pixmap(dpi=150)
                img_path = f"downloads/page_{page.number + 1}.jpg"
                pix.save(img_path)
                await update.message.reply_document(document=open(img_path, 'rb'))
            pdf_doc.close()
                
        elif file_extension in ['jpg', 'jpeg', 'png']:
            pdf_path = "downloads/converted_image.pdf"
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(file_path))
            await update.message.reply_document(document=open(pdf_path, 'rb'))
            
        elif file_extension == 'docx':
            doc_file = Document(file_path)
            text_content = "\n".join([p.text for p in doc_file.paragraphs if p.text])
            txt_path = "downloads/extracted_text.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            await update.message.reply_document(document=open(txt_path, 'rb'))
            
        else:
            await update.message.reply_text("عذراً، هذه الصيغة غير مدعومة حالياً.")
            
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الملف: {str(e)}")

if __name__ == '__main__':
    keep_alive() # تشغيل الخادم الوهمي لمنع التوقف
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("البوت يعمل الآن بنجاح...")
    application.run_polling()
