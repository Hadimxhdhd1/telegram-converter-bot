import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from pdf2image import convert_from_path
import img2pdf
from docx import Document
from openpyxl import Workbook, load_workbook

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("الرجاء إرسال ملف صالح (PDF, Word, Excel, JPG).")
        return

    doc = update.message.document
    file_name = doc.file_name
    file_extension = file_name.split('.')[-1].lower()
    
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", file_name)
    
    new_file = await context.bot.get_file(doc.file_id)
    await new_file.download_to_drive(file_path)
    
    await update.message.reply_text("⏳ جاري معالجة وتحويل الملف...")

    try:
        if file_extension == 'pdf':
            images = convert_from_path(file_path)
            for i, image in enumerate(images):
                img_path = f"downloads/page_{i+1}.jpg"
                image.save(img_path, 'JPEG')
                await update.message.reply_document(document=open(img_path, 'rb'))
                
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
            await update.message.reply_text("عذراً، هذه الصيغة غير مدعومة حالياً في التحويل المباشر.")
            
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الملف: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("البوت يعمل الآن بنجاح...")
    application.run_polling()
