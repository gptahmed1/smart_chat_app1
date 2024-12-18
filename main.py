import sys
import json
import google.generativeai as genai
import customtkinter as ctk
from dotenv import load_dotenv
import os
import threading

# تحميل المتغيرات البيئية
load_dotenv()

class MessageBubble(ctk.CTkFrame):
    def __init__(self, master, message, is_user=False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # إنشاء فقاعة الرسالة
        bubble = ctk.CTkFrame(
            self,
            fg_color="#383838" if is_user else "#2D2D2D",
            corner_radius=20
        )
        bubble.pack(side="right" if is_user else "left", fill="x", padx=20, pady=5)
        
        # إضافة الأيقونة
        icon_label = ctk.CTkLabel(
            bubble,
            text="👤" if is_user else "🤖",
            font=("Arial", 20),
            text_color="#FFFFFF"
        )
        icon_label.pack(side="right" if is_user else "left", padx=10, pady=10)
        
        # إضافة النص
        message_label = ctk.CTkLabel(
            bubble,
            text=message,
            font=("Arial", 16),
            text_color="#FFFFFF",
            wraplength=600,
            justify="right"
        )
        message_label.pack(side="right" if is_user else "left", padx=(10, 15), pady=10)

class SystemInstructionsDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, instructions=""):
        super().__init__(parent)
        self.title("💡 تعليمات عم ذكي")
        self.geometry("600x400")
        
        # إضافة شرح بسيط
        info_label = ctk.CTkLabel(
            self,
            text="اكتب هنا التعليمات اللي عايز عم ذكي يمشي عليها",
            font=("Arial", 14)
        )
        info_label.pack(pady=5)
        
        self.text_edit = ctk.CTkTextbox(
            self,
            font=("Arial", 14),
            wrap="word"
        )
        self.text_edit.pack(expand=True, fill="both", padx=10, pady=(5, 10))
        
        # تكوين محاذاة النص لليمين
        self.text_edit._textbox.tag_configure("right", justify="right")
        self.text_edit._textbox.insert("1.0", instructions)
        self.text_edit._textbox.tag_add("right", "1.0", "end")
        
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="تمام كده",
            command=self.save,
            font=("Arial", 14, "bold")
        )
        save_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="سيبك منه",
            command=self.cancel,
            font=("Arial", 14)
        )
        cancel_button.pack(side="right", padx=5)
        
        self.result = None
        
    def save(self):
        self.result = self.text_edit._textbox.get("1.0", "end-1c")
        self.destroy()
        
    def cancel(self):
        self.destroy()

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # إعداد النافذة الرئيسية
        self.title("عم ذكي 🤖")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # تعيين الألوان
        self.configure(fg_color="#1E1E1E")
        
        # تحميل الإعدادات
        self.system_instructions = ""
        self.chat_history = []
        self.messages_frame = None
        
        # إعداد Gemini
        self.setupGemini()
        
        # إعداد واجهة المستخدم
        self.setup_ui()
        
        # إضافة رسالة الترحيب
        welcome_msg = "👋 أهلاً بيك! أنا عم ذكي، المساعد الشخصي بتاعك.\nاسألني أي حاجة وأنا هساعدك!"
        self.add_message(welcome_msg, is_user=False)
        
    def setupGemini(self):
        """إعداد Gemini API"""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            self.show_error("الرجاء إضافة مفتاح API في ملف .env")
            return
        
        genai.configure(api_key=api_key)
        
        # إعدادات النموذج المتقدمة
        generation_config = {
            "temperature": 0.9,
            "top_p": 1.0,
            "top_k": 1,
            "max_output_tokens": 2048,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        self.model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إطار رئيسي
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # إطار المحادثة
        chat_frame = ctk.CTkFrame(main_frame, fg_color="#2D2D2D", corner_radius=15)
        chat_frame.pack(expand=True, fill="both", pady=(0, 10))
        
        # إطار للرسائل مع شريط التمرير
        messages_container = ctk.CTkScrollableFrame(
            chat_frame,
            fg_color="transparent",
            corner_radius=0
        )
        messages_container.pack(expand=True, fill="both", padx=5, pady=5)
        
        # حفظ مرجع لإطار الرسائل
        self.messages_frame = messages_container
        
        # منطقة الإدخال
        input_frame = ctk.CTkFrame(main_frame, fg_color="#2D2D2D", corner_radius=15, height=100)
        input_frame.pack(fill="x")
        input_frame.pack_propagate(False)
        
        # إطار داخلي للمدخلات
        inner_input_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        inner_input_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # زر الميكروفون
        mic_button = ctk.CTkButton(
            inner_input_frame,
            text="🎤",
            width=40,
            fg_color="transparent",
            hover_color="#3D3D3D",
            font=("Arial", 20)
        )
        mic_button.pack(side="left", padx=(5, 10))
        
        # منطقة إدخال النص
        self.input_area = ctk.CTkTextbox(
            inner_input_frame,
            font=("Arial", 16),
            wrap="word",
            fg_color="#1E1E1E",
            text_color="#FFFFFF",
            border_width=0,
            height=60
        )
        self.input_area.pack(side="left", expand=True, fill="both", padx=5)
        self.input_area.bind("<Return>", self.on_return)
        
        # زر الإرسال
        self.send_button = ctk.CTkButton(
            inner_input_frame,
            text="➤",
            width=40,
            fg_color="transparent",
            hover_color="#3D3D3D",
            font=("Arial", 20),
            command=self.send_message
        )
        self.send_button.pack(side="right", padx=(10, 5))
        
        # إطار الأزرار
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.clear_button = ctk.CTkButton(
            button_frame,
            text="مسح المحادثة",
            command=self.clear_chat,
            font=("Arial", 14)
        )
        self.clear_button.pack(side="right", padx=5)
        
        self.instructions_button = ctk.CTkButton(
            button_frame,
            text="تعليمات النظام",
            command=self.edit_instructions,
            font=("Arial", 14)
        )
        self.instructions_button.pack(side="right", padx=5)
        
    def show_error(self, message):
        """عرض رسالة خطأ"""
        dialog = ctk.CTkInputDialog(
            text=message,
            title="في مشكلة 😕",
            button_text="تمام"
        )
        dialog.geometry("400x200")
        dialog.destroy()
        
    def on_return(self, event):
        """معالجة ضغط Enter"""
        if not event.state & 0x1:  # التحقق من عدم الضغط على Shift
            self.send_message()
            return "break"
        return None
        
    def add_message(self, message, is_user=False):
        """إضافة رسالة"""
        message_bubble = MessageBubble(self.messages_frame, message, is_user)
        message_bubble.pack(fill="x", padx=10, pady=5)
        
    def send_message(self):
        """إرسال رسالة"""
        user_input = self.input_area._textbox.get("1.0", "end-1c").strip()
        if not user_input:
            return
            
        # تعطيل زر الإرسال أثناء المعالجة
        self.send_button.configure(state="disabled", text="⌛")
        self.input_area.configure(state="disabled")
        
        # إنشاء مهمة جديدة للمعالجة
        threading.Thread(target=self._process_message, args=(user_input,), daemon=True).start()
    
    def _process_message(self, user_input):
        """معالجة الرسالة في خيط منفصل"""
        try:
            # إضافة رسالة المستخدم
            self.add_message(user_input, is_user=True)
            self.input_area._textbox.delete("1.0", "end")
            
            # تجهيز الطلب
            prompt = user_input
            if self.system_instructions:
                context = "\n".join([msg for msg in self.chat_history[-3:]])
                prompt = f"{self.system_instructions}\n\nالمحادثة السابقة:\n{context}\n\nالمستخدم: {user_input}"
            
            # إضافة علامة "جاري الكتابة..."
            typing_message = self.add_message("جاري الكتابة...", is_user=False)
            
            # إرسال الطلب للنموذج بشكل متزامن مع تحسين الأداء
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            )
            
            if response.text:
                # حذف علامة "جاري الكتابة..."
                if typing_message:
                    typing_message.destroy()
                
                # إضافة رد المساعد
                self.add_message(response.text, is_user=False)
                
                # حفظ المحادثة
                self.chat_history.append(f"المستخدم: {user_input}")
                self.chat_history.append(f"عم ذكي: {response.text}")
                
                # تحديث السياق للحفاظ على الأداء
                if len(self.chat_history) > 6:  # الاحتفاظ بآخر 3 محادثات فقط
                    self.chat_history = self.chat_history[-6:]
            else:
                raise Exception("معلش يا باشا، مش قادر أرد دلوقتي")
            
        except Exception as e:
            error_msg = str(e)
            if "400 Bad Request" in error_msg:
                error_msg = "في مشكلة في الاتصال، تأكد من مفتاح API"
            elif "429 Too Many Requests" in error_msg:
                error_msg = "براحة شوية، في ضغط على السيرفر. جرب تاني بعد شوية"
            
            # حذف علامة "جاري الكتابة..."
            if typing_message:
                typing_message.destroy()
            
            self.add_message(f"⚠️ في مشكلة: {error_msg}", is_user=False)
        
        finally:
            # إعادة تفعيل عناصر التحكم
            self.send_button.configure(state="normal", text="➤")
            self.input_area.configure(state="normal")
            self.input_area.focus()
            
    def clear_chat(self):
        """مسح المحادثة"""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.chat_history = []  # مسح سجل المحادثة
        
        # إضافة رسالة ترحيب
        welcome_msg = "👋 أهلاً بيك! أنا عم ذكي، المساعد الشخصي بتاعك.\nاسألني أي حاجة وأنا هساعدك!"
        self.add_message(welcome_msg, is_user=False)
        
    def edit_instructions(self):
        """تعديل تعليمات النظام"""
        dialog = SystemInstructionsDialog(self, self.system_instructions)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.system_instructions = dialog.result

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    app = ChatApp()
    app.mainloop()
