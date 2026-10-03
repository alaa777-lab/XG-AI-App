import os
import base64
import flet as ft
from google import genai
from google.genai import types

def main(page: ft.Page):
    # ------------------ إعدادات الثيم والواجهة الفخمة ------------------
    page.title = "XG AI - Super Assistant"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#0B0F19"
    
    # ⚠️ ضع مفتاح API الخاص بك هنا بين التنصيص
    API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6LXfDICxKnOYck0AiJBH93L0D8SXSi31o_EB-sJEFrB-Q")
    
    chat_history = []
    selected_file_data = {"bytes": None, "name": None, "mime": None}

    # ------------------ عناصر الواجهة العلوية ------------------
    selected_mode = "General"
    
    def set_mode(e):
        nonlocal selected_mode
        selected_mode = e.control.value
        page.show_snack_bar(ft.SnackBar(ft.Text(f"النمط الحالي: {selected_mode}"), open=True))

    mode_dropdown = ft.Dropdown(
        value="General",
        width=140,
        bgcolor="#1E2640",
        color="#A855F7",
        border_radius=12,
        options=[
            ft.dropdown.Option("General", "🌐 محادثة"),
            ft.dropdown.Option("ImageGen", "🎨 توليد صور"),
            ft.dropdown.Option("Coder", "💻 مبرمج"),
        ],
        on_change=set_mode
    )

    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color="#A855F7", size=28),
                ft.Text("XG AI", size=24, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ]),
            mode_dropdown
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.only(left=15, right=15, top=35, bottom=12),
        bgcolor="#111827",
        border=ft.border.only(bottom=ft.BorderSide(1, "#1F2937"))
    )

    chat_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)
    chat_container = ft.Container(content=chat_list, padding=15, expand=True)

    # ------------------ معالجة رفع الملفات والصور ------------------
    file_preview_text = ft.Text("", size=11, color="#A855F7", visible=False)

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            picked_file = e.files[0]
            with open(picked_file.path, "rb") as f:
                selected_file_data["bytes"] = f.read()
            selected_file_data["name"] = picked_file.name
            
            # تحديد النوع المصدري للملف
            if picked_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                selected_file_data["mime"] = f"image/{picked_file.name.split('.')[-1]}"
            else:
                selected_file_data["mime"] = "text/plain"
                
            file_preview_text.value = f"📎 تم إرفاق: {picked_file.name}"
            file_preview_text.visible = True
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # ------------------ أدوات مساعدة ------------------
    def copy_text(text):
        page.set_clipboard(text)
        page.show_snack_bar(ft.SnackBar(ft.Text("تم النسخ إلى الحافظة! 📋"), open=True))

    # ------------------ إرسال الطلب وإدارة النتائج ------------------
    def send_message(e):
        prompt = user_input.value.strip()
        if not prompt and not selected_file_data["bytes"]:
            return

        user_input.value = ""
        file_preview_text.visible = False
        page.update()

        # 1. إظهار رسالة المستخدم
        user_msg_content = [
            ft.Text("أنت", size=11, color="#9CA3AF", weight=ft.FontWeight.BOLD),
            ft.Text(prompt if prompt else "تحليل الملف المرفق...", color="#FFFFFF", size=15)
        ]
        
        if selected_file_data["name"]:
            user_msg_content.append(ft.Text(f"📎 {selected_file_data['name']}", size=12, color="#38BDF8"))

        chat_list.controls.append(
            ft.Container(
                content=ft.Column(user_msg_content),
                alignment=ft.alignment.center_right,
                bgcolor="#6D28D9",
                padding=14,
                border_radius=ft.border_radius.only(top_left=16, top_right=16, bottom_left=16),
                margin=ft.margin.only(left=30)
            )
        )
        
        # 2. مؤشر الانتظار
        loading_card = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2, color="#A855F7"),
                ft.Text("XG AI يعالج الطلب...", color="#9CA3AF", italic=True)
            ]),
            bgcolor="#1F2937",
            padding=10,
            border_radius=10
        )
        chat_list.controls.append(loading_card)
        page.update()

        # 3. الاتصال بـ Google AI Studio
        try:
            client = genai.Client(api_key=API_KEY)

            # --- وضع توليد الصور (ImageGen) ---
            if selected_mode == "ImageGen":
                imagen_resp = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/jpeg",
                        aspect_ratio="1:1"
                    )
                )
                
                # استخراج الصورة المولدّة بصيغة Base64
                img_bytes = imagen_resp.generated_images[0].image.image_bytes
                base64_img = base64.b64encode(img_bytes).decode('utf-8')
                
                chat_list.controls.remove(loading_card)
                chat_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("XG AI - الصورة المولدة 🎨", size=12, color="#A855F7", weight=ft.FontWeight.BOLD),
                            ft.Image(src_base64=base64_img, width=300, height=300, fit=ft.ImageFit.CONTAIN, border_radius=12)
                        ]),
                        bgcolor="#111827",
                        padding=14,
                        border_radius=16,
                        border=ft.border.all(1, "#1F2937")
                    )
                )

            # --- الوضع النصي وتحليل الصور والملفات ---
            else:
                contents_payload = []
                
                if selected_file_data["bytes"]:
                    contents_payload.append(
                        types.Part.from_bytes(
                            data=selected_file_data["bytes"],
                            mime_type=selected_file_data["mime"]
                        )
                    )
                
                contents_payload.append(prompt)
                
                sys_inst = "أنت XG AI، ذكاء اصطناعي فاخر وذكي كـ Gemini، أجب بوضوح وتنسيق ممتاز."
                if selected_mode == "Coder":
                    sys_inst = "أنت XG AI Coder، خبير برمجة يكتب أكواداً نظيفة ومشروحة."

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_inst,
                        temperature=0.3
                    )
                )
                
                bot_reply = response.text
                chat_list.controls.remove(loading_card)

                # عرض الإجابة مع أزرار التحكم
                chat_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Row([
                                    ft.Icon(ft.Icons.AUTO_AWESOME, color="#A855F7", size=16),
                                    ft.Text("XG AI", size=12, color="#A855F7", weight=ft.FontWeight.BOLD),
                                ]),
                                ft.IconButton(
                                    icon=ft.Icons.COPY_ROUNDED,
                                    icon_color="#9CA3AF",
                                    icon_size=18,
                                    tooltip="نسخ",
                                    on_click=lambda _: copy_text(bot_reply)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Markdown(bot_reply, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
                        ]),
                        bgcolor="#111827",
                        padding=16,
                        border_radius=ft.border_radius.only(top_left=16, top_right=16, bottom_right=16),
                        border=ft.border.all(1, "#1F2937"),
                        margin=ft.margin.only(right=15)
                    )
                )

        except Exception as err:
            chat_list.controls.remove(loading_card)
            chat_list.controls.append(
                ft.Container(
                    content=ft.Text(f"❌ خطأ: {str(err)}", color="#EF4444"),
                    bgcolor="#111827",
                    padding=12,
                    border_radius=10
                )
            )

        # إعادة ضبط الملف المرفق
        selected_file_data["bytes"] = None
        selected_file_data["name"] = None
        selected_file_data["mime"] = None
        page.update()

    # ------------------ شريط المدخلات السفلي ------------------
    user_input = ft.TextField(
        hint_text="اسأل XG AI أو اطلب صورة...",
        fill_color="#111827",
        filled=True,
        border_radius=22,
        expand=True,
        border_color="#1F2937",
        focused_border_color="#A855F7",
        cursor_color="#A855F7",
        color="#FFFFFF",
        on_submit=send_message
    )

    attach_btn = ft.IconButton(
        icon=ft.Icons.ATTACH_FILE_ROUNDED,
        icon_color="#9CA3AF",
        tooltip="إرفاق صورة/ملف",
        on_click=lambda _: file_picker.pick_files()
    )

    send_btn = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD_ROUNDED,
            icon_color="#FFFFFF",
            icon_size=20,
            on_click=send_message
        ),
        bgcolor="#A855F7",
        shape=ft.BoxShape.CIRCLE,
    )

    input_bar = ft.Container(
        content=ft.Column([
            file_preview_text,
            ft.Row([attach_btn, user_input, send_btn], spacing=8)
        ]),
        padding=ft.padding.only(left=10, right=10, top=8, bottom=20),
        bgcolor="#0B0F19",
        border=ft.border.only(top=ft.BorderSide(1, "#1F2937"))
    )

    page.add(header, chat_container, input_bar)

# تشغيل التطبيق في المتصفح بالتوافق مع التحديثات الجديدة
ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8080)

