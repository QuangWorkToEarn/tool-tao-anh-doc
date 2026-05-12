import streamlit as st
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import io
import zipfile
import urllib.request
import textwrap
import google.generativeai as genai

st.set_page_config(page_title="Bot Xử Lý Ảnh Pro", page_icon="📱", layout="wide")
st.title("📱 Hệ Thống Xử Lý Ảnh Tự Động")

# Tải Font tiếng Việt trực tiếp từ nguồn siêu ổn định (Tránh lỗi 404)
@st.cache_resource(show_spinner="Đang nạp Font chữ chuẩn Tiếng Việt...")
def load_vietnamese_font():
    # Sử dụng kho mã nguồn tĩnh, không bị thay đổi cấu trúc như Google Fonts
    url = "https://raw.githubusercontent.com/openmaptiles/fonts/master/roboto/Roboto-Bold.ttf"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    return response.read()

# Chia giao diện làm 2 Tab
tab1, tab2 = st.tabs(["⚙️ Cắt Ghép Cơ Bản (Tốc độ cao)", "✨ AI Việt Hóa & Bố Cục (Tự động)"])

# ==========================================
# TAB 1: TOOL CẮT GHÉP CƠ BẢN NHƯ CŨ
# ==========================================
with tab1:
    st.markdown("💡 **Mẹo:** Kéo thả hàng loạt ảnh vào đây để tự động bo viền mờ theo tỷ lệ.")
    
    ratio_choice = st.selectbox(
        "📐 Chọn định dạng ảnh đầu ra:", 
        ["9:16 (Chuẩn Video dọc: TikTok, Shorts, Reels)", "1:1 (Chuẩn Ảnh vuông: Sản phẩm, POD)"],
        key="tab1_ratio"
    )

    if ratio_choice.startswith("9:16"):
        TARGET_WIDTH, TARGET_HEIGHT, file_prefix = 1080, 1920, "916_"
    else:
        TARGET_WIDTH, TARGET_HEIGHT, file_prefix = 1080, 1080, "11_"

    uploaded_files = st.file_uploader("Kéo thả ảnh vào đây", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp'], key="tab1_upload")

    if uploaded_files:
        if st.button("🚀 Xử Lý Cắt Ghép", type="primary", key="tab1_btn"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)
            total_files = len(uploaded_files)
            
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for i, file in enumerate(uploaded_files):
                    try:
                        img = Image.open(file).convert("RGB")
                        img_w, img_h = img.size

                        bg_ratio = max(TARGET_WIDTH / img_w, TARGET_HEIGHT / img_h)
                        bg_img = img.resize((int(img_w * bg_ratio), int(img_h * bg_ratio)), Image.Resampling.LANCZOS)
                        left = (bg_img.width - TARGET_WIDTH) / 2
                        top = (bg_img.height - TARGET_HEIGHT) / 2
                        bg_img = bg_img.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))
                        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=30))

                        fg_ratio = min(TARGET_WIDTH / img_w, TARGET_HEIGHT / img_h)
                        fg_img = img.resize((int(img_w * fg_ratio), int(img_h * fg_ratio)), Image.Resampling.LANCZOS)

                        offset_x = (TARGET_WIDTH - fg_img.width) // 2
                        offset_y = (TARGET_HEIGHT - fg_img.height) // 2
                        bg_img.paste(fg_img, (offset_x, offset_y))

                        img_byte_arr = io.BytesIO()
                        bg_img.save(img_byte_arr, format='JPEG', quality=95)
                        
                        file_name = file.name if file.name else f"image_{i}.jpg"
                        zip_file.writestr(f"{file_prefix}{file_name}", img_byte_arr.getvalue())
                        progress_bar.progress((i + 1) / total_files)
                        
                    except Exception as e:
                        st.error(f"Lỗi file {file.name}: {e}")

            st.success("🎉 Đã xử lý xong!")
            st.download_button("📦 Tải tất cả ảnh về (.zip)", data=zip_buffer.getvalue(), file_name=f"anh_xuly_{file_prefix[:-1]}.zip", mime="application/zip")


# ==========================================
# TAB 2: TOOL AI ĐỌC DỊCH VÀ CHÈN TEXT TỰ ĐỘNG
# ==========================================
with tab2:
    st.markdown("💡 **Tính năng AI (Bóc Tách & Việt Hóa):** Tự động đọc chữ nước ngoài, dịch sang câu Hook tiếng Việt và chèn vào giữa vùng an toàn 9:16.")
    
    api_key_input = st.text_input("🔑 Nhập Gemini API Key của bạn:", type="password")
    ai_uploaded_files = st.file_uploader("Tải ảnh cần Việt Hóa (Xiaohongshu, Douyin...)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="tab2_upload")
    
    default_prompt = "Hãy đọc các chữ chính trong bức ảnh này, dịch nó sang tiếng Việt. Rút gọn thành 1 câu tiêu đề cực kỳ giật gân, thu hút để bán hàng (dưới 15 chữ). CHỈ TRẢ VỀ NỘI DUNG TEXT, KHÔNG GIẢI THÍCH."
    ai_prompt = st.text_area("🤖 Lệnh cho AI (Prompt):", value=default_prompt, height=100)

    if ai_uploaded_files and ai_prompt and api_key_input:
        if st.button("✨ Bắt Đầu Việt Hóa Ảnh", type="primary", key="tab2_btn"):
            try:
                genai.configure(api_key=api_key_input)
                # Dùng Gemini 1.5 Pro siêu đỉnh trong việc đọc hiểu ảnh và dịch thuật
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                st.info("Đang xử lý... AI đang dịch và hệ thống đang dàn lại bố cục chuẩn TikTok 🚀")
                ai_zip_buffer = io.BytesIO()
                
                # Tải Font tiếng Việt
                font_bytes = load_vietnamese_font()
                font = ImageFont.truetype(io.BytesIO(font_bytes), size=60)
                
                with zipfile.ZipFile(ai_zip_buffer, "w") as ai_zip_file:
                    for i, file in enumerate(ai_uploaded_files):
                        img = Image.open(file).convert("RGB")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img, caption=f"🖼️ Ảnh Gốc: {file.name}", use_column_width=True)
                            
                        # 1. Gọi AI để lấy Text Tiếng Việt
                        response = model.generate_content([ai_prompt, img])
                        vi_text = response.text.strip().replace('"', '')
                        
                        # 2. Tạo phôi ảnh 9:16 (Xóa mờ viền)
                        TARGET_WIDTH, TARGET_HEIGHT = 1080, 1920
                        img_w, img_h = img.size
                        
                        bg_ratio = max(TARGET_WIDTH / img_w, TARGET_HEIGHT / img_h)
                        bg_img = img.resize((int(img_w * bg_ratio), int(img_h * bg_ratio)), Image.Resampling.LANCZOS)
                        left = (bg_img.width - TARGET_WIDTH) / 2
                        top = (bg_img.height - TARGET_HEIGHT) / 2
                        bg_img = bg_img.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))
                        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=30))

                        fg_ratio = min(TARGET_WIDTH / img_w, TARGET_HEIGHT / img_h)
                        fg_img = img.resize((int(img_w * fg_ratio), int(img_h * fg_ratio)), Image.Resampling.LANCZOS)
                        offset_x = (TARGET_WIDTH - fg_img.width) // 2
                        offset_y = (TARGET_HEIGHT - fg_img.height) // 2
                        bg_img.paste(fg_img, (offset_x, offset_y))
                        
                        # 3. Tính toán Text và Xuống dòng tự động
                        wrapper = textwrap.TextWrapper(width=22) 
                        wrapped_text = wrapper.fill(text=vi_text)
                        
                        draw = ImageDraw.Draw(bg_img)
                        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center')
                        text_w = bbox[2] - bbox[0]
                        text_h = bbox[3] - bbox[1]
                        
                        # Căn giữa tấm ảnh
                        x = (TARGET_WIDTH - text_w) / 2
                        y = (TARGET_HEIGHT - text_h) / 2
                        
                        # 4. Vẽ dải nền đen mờ (Overlay) ôm lấy chữ để che hình cũ và làm chữ nổi bật
                        pad = 50 # Độ rộng lề của dải đen
                        overlay = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
                        overlay_draw = ImageDraw.Draw(overlay)
                        # Vẽ hình chữ nhật từ viền trái qua viền phải, ở giữa màn hình
                        overlay_draw.rectangle([0, y - pad, TARGET_WIDTH, y + text_h + pad], fill=(0, 0, 0, 170))
                        
                        bg_img = bg_img.convert('RGBA')
                        final_img = Image.alpha_composite(bg_img, overlay)
                        
                        # 5. Vẽ Chữ Tiếng Việt lên trên cùng
                        final_draw = ImageDraw.Draw(final_img)
                        final_draw.multiline_text((x, y), wrapped_text, font=font, fill=(255, 255, 255), align='center')
                        final_img = final_img.convert('RGB')
                        
                        with col2:
                            st.image(final_img, caption=f"✨ Ảnh Mới Đã Xử Lý", use_column_width=True)
                        
                        # Lưu vào ZIP
                        img_byte_arr = io.BytesIO()
                        final_img.save(img_byte_arr, format='JPEG', quality=95)
                        file_name = file.name if file.name else f"ai_image_{i}.jpg"
                        ai_zip_file.writestr(f"AI_VietHoa_{file_name}", img_byte_arr.getvalue())
                
                st.success("🎉 Đã Việt hóa và dàn layout xong!")
                st.download_button("📦 Tải Ảnh Đã Xử Lý Về (.zip)", data=ai_zip_buffer.getvalue(), file_name="anh_ai_viethoa.zip", mime="application/zip", key="tab2_download")
                
            except Exception as e:
                st.error(f"❌ Có lỗi khi gọi AI hoặc Xử lý ảnh: {e}")
