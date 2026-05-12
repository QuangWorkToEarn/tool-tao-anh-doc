import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import urllib.request

# Sử dụng thư viện hệ GenAI MỚI NHẤT của Google
from google import genai
from google.genai import types

st.set_page_config(page_title="Bot Xử Lý Ảnh Pro", page_icon="📱", layout="wide")
st.title("📱 Hệ Thống Xử Lý Ảnh Tự Động")

# Tải Font tiếng Việt trực tiếp từ nguồn siêu ổn định
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
    st.markdown("💡 **Tính năng Sáng tạo (Dual-Engine):** Tự do lựa chọn Model từ API Key của bạn để vẽ lại ảnh.")
    
    api_key_input = st.text_input("🔑 Nhập Gemini API Key của bạn:", type="password")
    
    # KHI NHẬP API KEY SẼ TỰ ĐỘNG GỌI LIST MODELS
    if api_key_input:
        try:
            client = genai.Client(api_key=api_key_input)
            raw_models = list(client.models.list())
            model_names = [m.name for m in raw_models]
            
            st.success(f"✅ Đã quét thành công {len(model_names)} models từ API Key của bạn!")
            
            # Giao diện cho người dùng tự chọn Model
            with st.expander("🛠️ Cấu hình AI Thủ công (Bấm để chọn)", expanded=True):
                col_v, col_i = st.columns(2)
                
                # Cố gắng tìm gemini-2.5-flash làm mặc định cho Não bộ, nếu không có thì lấy cái đầu tiên
                default_v_index = model_names.index('models/gemini-2.5-flash') if 'models/gemini-2.5-flash' in model_names else 0
                vision_choice = col_v.selectbox("🧠 Model Phân tích (Não bộ):", model_names, index=default_v_index)
                
                # Cố gắng tìm imagen hoặc các model image của bạn làm mặc định
                default_i_index = 0
                for i, name in enumerate(model_names):
                    if 'image' in name or 'banana' in name or 'imagen' in name:
                        default_i_index = i
                        break
                image_choice = col_i.selectbox("🎨 Model Vẽ Ảnh (Họa sĩ):", model_names, index=default_i_index)

            ai_uploaded_files = st.file_uploader("Tải ảnh gốc dùng làm Concept", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
            ai_prompt = st.text_area("🤖 Lệnh cho AI:", value="Đổi áo của nhân vật sang màu xanh lá. In dòng chữ 'HACK CHIỀU CAO 1M65' to và rõ ràng ở dưới.", height=100)

            if ai_uploaded_files and ai_prompt:
                if st.button("✨ Phân Tích & Vẽ Lại Ảnh Mới", type="primary"):
                    try:
                        ai_zip_buffer = io.BytesIO()
                        progress_bar_ai = st.progress(0)
                        total_files = len(ai_uploaded_files)
                        
                        with zipfile.ZipFile(ai_zip_buffer, "w") as ai_zip_file:
                            for i, file in enumerate(ai_uploaded_files):
                                img = Image.open(file).convert("RGB")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.image(img, caption="🖼️ Concept Gốc", use_column_width=True)
                                
                                # --- BƯỚC 1: Phân tích ---
                                st.write(f"🧠 Đang dùng {vision_choice} để phân tích...")
                                system_prompt = f"Analyze the attached image in extreme detail. Integrate the user's specific request: '{ai_prompt}'. Write ONLY a comprehensive English prompt for an AI image generator."
                                
                                # Bỏ chữ 'models/' để tương thích với SDK mới
                                v_clean = vision_choice.replace('models/', '')
                                i_clean = image_choice.replace('models/', '')
                                
                                vision_response = client.models.generate_content(
                                    model=v_clean,
                                    contents=[system_prompt, img]
                                )
                                master_prompt = vision_response.text.strip()
                                
                                # --- BƯỚC 2: Vẽ ảnh ---
                                st.write(f"🎨 Đang dùng {image_choice} để vẽ...")
                                image_response = client.models.generate_images(
                                    model=i_clean,
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
                                        st.image(ai_output_img, caption="✨ Thành Phẩm", use_column_width=True)
                                    
                                    img_byte_arr = io.BytesIO()
                                    ai_output_img.save(img_byte_arr, format='JPEG', quality=95)
                                    file_name = file.name if file.name else f"ai_generated_{i}.jpg"
                                    ai_zip_file.writestr(f"AI_ReCreated_{file_name}", img_byte_arr.getvalue())
                                
                                progress_bar_ai.progress((i + 1) / total_files)
                        
                        st.success("🎉 Đã sáng tạo xong!")
                        st.download_button("📦 Tải Ảnh Về", data=ai_zip_buffer.getvalue(), file_name="anh_ai_vedep.zip", mime="application/zip")
                        
                    except Exception as e:
                        st.error(f"❌ Có lỗi trong quá trình chạy Model: {e}")
                        st.info("💡 Mẹo: Lỗi 'not supported for predict' nghĩa là Model bạn vừa chọn ở Menu thả xuống chưa được Google cấp quyền vẽ ảnh. Hãy thử chọn một Model khác có chữ 'image' hoặc 'imagen' trong danh sách nhé.")
                        
        except Exception as e:
            st.error(f"❌ Lỗi kết nối quét danh sách API: {e}")
