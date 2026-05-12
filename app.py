import streamlit as st
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import io
import zipfile
import urllib.request
import textwrap

# Chuyển sang sử dụng thư viện hệ GenAI MỚI NHẤT của Google
from google import genai
from google.genai import types

st.set_page_config(page_title="Bot Xử Lý Ảnh Pro", page_icon="📱", layout="wide")
st.title("📱 Hệ Thống Xử Lý Ảnh Tự Động")

# Tải Font tiếng Việt trực tiếp từ nguồn siêu ổn định (Tránh lỗi 404)
@st.cache_resource(show_spinner="Đang nạp Font chữ chuẩn Tiếng Việt...")
def load_vietnamese_font():
    url = "https://raw.githubusercontent.com/openmaptiles/fonts/master/roboto/Roboto-Bold.ttf"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    return response.read()

# Chia giao diện làm 2 Tab
tab1, tab2 = st.tabs(["⚙️ Cắt Ghép Cơ Bản (Tốc độ cao)", "✨ Trợ Lý Sáng Tạo Ảnh AI (Tái Tạo Mới)"])

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
# TAB 2: TRỢ LÝ SÁNG TẠO ẢNH AI (TÁI TẠO MỚI)
# ==========================================
with tab2:
    st.markdown("💡 **Tính năng Sáng tạo (Dual-Engine):** AI sẽ đọc concept ảnh cũ, tiếp nhận yêu cầu đổi màu/chi tiết của bạn, và tự động vẽ ra một bức ảnh MỚI TINH, lách 100% quét bản quyền!")
    
    api_key_input = st.text_input("🔑 Nhập Gemini API Key của bạn:", type="password")
    ai_uploaded_files = st.file_uploader("Tải ảnh gốc dùng làm Concept", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="tab2_upload")
    
    default_prompt = "Dựa trên bức ảnh này, hãy đổi áo của nhân vật sang màu xanh lá cây đậm. In dòng chữ 'HACK CHIỀU CAO 1M65' to và rõ ràng ở khoảng trống phía dưới."
    ai_prompt = st.text_area("🤖 Lệnh cho AI (Ví dụ: thay đổi màu sắc trang phục, thêm chữ):", value=default_prompt, height=100)

    if ai_uploaded_files and ai_prompt and api_key_input:
        if st.button("✨ Phân Tích & Vẽ Lại Ảnh Mới", type="primary", key="tab2_btn"):
            try:
                # Gọi client mới theo chuẩn google-genai
                client = genai.Client(api_key=api_key_input)
                
                st.info("🔍 Đang nạp hệ thống phân tích và hệ thống đồ họa chuẩn SDK mới...")
                ai_zip_buffer = io.BytesIO()
                progress_bar_ai = st.progress(0)
                total_files = len(ai_uploaded_files)
                
                with zipfile.ZipFile(ai_zip_buffer, "w") as ai_zip_file:
                    for i, file in enumerate(ai_uploaded_files):
                        img = Image.open(file).convert("RGB")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img, caption=f"🖼️ Concept Gốc", use_column_width=True)
                        
                        # --- BƯỚC 1: Dùng Vision Model phân tích ảnh và tạo Master Prompt ---
                        st.write("🧠 Đang phân tích phong cách ảnh và dịch yêu cầu...")
                        system_prompt = f"Analyze the attached image in extreme detail (art style, character features, pose, lighting, background). Then, integrate the user's specific request: '{ai_prompt}'. Write ONLY a comprehensive English prompt for an AI image generator to recreate this exact style and scene, applying the requested changes (like shirt color and text overlays). Ensure text requests are wrapped in quotes."
                        
                        vision_response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[system_prompt, img]
                        )
                        master_prompt = vision_response.text.strip()
                        
                        # --- BƯỚC 2: Dùng Image Model (Imagen 3) để vẽ ảnh mới ---
                        st.write("🎨 Đang vẽ lại bức tranh mới tinh...")
                        
                        image_response = client.models.generate_images(
                            model='imagen-3.0-generate-001',
                            prompt=master_prompt,
                            config=types.GenerateImagesConfig(
                                number_of_images=1,
                                output_mime_type="image/jpeg",
                                aspect_ratio="3:4" 
                            )
                        )
                        
                        ai_output_img = image_response.generated_images[0].image
                            
                        if ai_output_img:
                            with col2:
                                st.image(ai_output_img, caption=f"✨ Thành Phẩm (AI Đã Vẽ Lại)", use_column_width=True)
                            
                            # Lưu vào ZIP
                            img_byte_arr = io.BytesIO()
                            ai_output_img.save(img_byte_arr, format='JPEG', quality=95)
                            file_name = file.name if file.name else f"ai_generated_{i}.jpg"
                            ai_zip_file.writestr(f"AI_ReCreated_{file_name}", img_byte_arr.getvalue())
                        
                        progress_bar_ai.progress((i + 1) / total_files)
                
                st.success("🎉 Đã sáng tạo xong toàn bộ mẫu mới!")
                st.download_button("📦 Tải Ảnh Siêu Phẩm Về (.zip)", data=ai_zip_buffer.getvalue(), file_name="anh_ai_vedep.zip", mime="application/zip", key="tab2_download")
                
            except Exception as e:
                st.error(f"❌ Có lỗi trong quá trình sáng tạo: {e}")
