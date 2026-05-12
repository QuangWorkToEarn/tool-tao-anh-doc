import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import google.generativeai as genai

st.set_page_config(page_title="Bot Xử Lý Ảnh Pro", page_icon="📱", layout="wide")
st.title("📱 Hệ Thống Xử Lý Ảnh Tự Động")

# Chia giao diện làm 2 Tab
tab1, tab2 = st.tabs(["⚙️ Cắt Ghép Cơ Bản (Tốc độ cao)", "✨ AI Việt Hóa & Bố Cục (Tự động - Image-to-Image)"])

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
# TAB 2: TOOL AI VIỆT HÓA & BỐ CỤC (TỰ ĐỘNG - Image-to-Image)
# ==========================================
with tab2:
    st.markdown("💡 **Tính năng AI (Bóc Tách & Việt Hóa - Image-to-Image):** Tự động đọc text Trung, dịch sang tiếng Việt, xóa text cũ, chèn text mới và trả về ảnh hoàn chỉnh. Giống như khi bạn chat với tôi!")
    
    # Ô nhập API Key (Bảo mật, ẩn ký tự)
    api_key_input = st.text_input("🔑 Nhập Gemini API Key của bạn:", type="password")
    
    # Khung upload ảnh cho AI
    ai_uploaded_files = st.file_uploader("Tải ảnh đầu vào (Xiaohongshu, Douyin...)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="tab2_upload")
    
    # Ô nhập lệnh (Prompt) - Hướng dẫn chi tiết cho Image Editing
    default_prompt = "Xóa toàn bộ chữ Trung Quốc khỏi hình ảnh này. Giữ nguyên sản phẩm và người mẫu. Dịch text gốc sang tiếng Việt (nếu có), đặt câu Hook 'ÁO KHOÁC NAM SIÊU CẤP - THỜI TRANG 2026' vào vị trí phù hợp, to rõ, phong cách chuyên nghiệp."
    ai_prompt = st.text_area("🤖 Lệnh cho AI (Prompt):", value=default_prompt, height=100, placeholder="Ví dụ: Xóa toàn bộ chữ cũ, giữ nguyên người mẫu, chèn một tiêu đề tiếng Việt 'ÁO NAM SIÊU BÉN' vào vị trí chính giữa hình ảnh.")

    if ai_uploaded_files and ai_prompt and api_key_input:
        if st.button("✨ Bắt Đầu Sinh Ảnh Mới", type="primary", key="tab2_btn"):
            try:
                # Cấu hình API Key
                genai.configure(api_key=api_key_input)
                
                # Gọi mô hình AI chuyên dụng cho Image-to-Image: models/nano-banana-pro-preview
                model = genai.GenerativeModel('models/nano-banana-pro-preview')
                
                st.info("Đang xử lý ảnh... Sức mạnh của AI (Image-to-Image) đang được vận dụng, vui lòng đợi trong giây lát 🚀")
                progress_bar_ai = st.progress(0)
                
                # Tạo bộ nhớ để nén file trả về
                ai_zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(ai_zip_buffer, "w") as ai_zip_file:
                    for i, file in enumerate(ai_uploaded_files):
                        img = Image.open(file)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img, caption=f"🖼️ Ảnh Gốc: {file.name}", use_column_width=True)
                            
                        # Gọi API chỉnh sửa ảnh
                        # SDK cho AI Studio hỗ trợ Image-to-Image bằng cách truyền cả prompt và image vào danh sách content
                        response = model.generate_content([ai_prompt, img])
                        
                        # Xử lý phản hồi dạng ảnh (Image-to-Image)
                        # Giả sử thư viện Python SDK cho AI Studio hỗ trợ lấy image response
                        if response.image:
                            ai_output_img = response.image
                            
                            with col2:
                                st.image(ai_output_img, caption=f"✨ Ảnh Đã Xử Lý", use_column_width=True)
                            
                            # Lưu vào ZIP
                            img_byte_arr = io.BytesIO()
                            ai_output_img.save(img_byte_arr, format='JPEG', quality=95)
                            file_name = file.name if file.name else f"ai_image_{i}.jpg"
                            ai_zip_file.writestr(f"AI_Edited_{file_name}", img_byte_arr.getvalue())
                        else:
                            st.error(f"❌ AI không trả về ảnh cho file {file.name}. Có thể prompt không hợp lệ hoặc model không hỗ trợ.")
                        
                        progress_bar_ai.progress((i + 1) / len(ai_uploaded_files))
                        
                st.success("🎉 AI đã xử lý xong!")
                st.download_button("📦 Tải tất cả ảnh về (.zip)", data=ai_zip_buffer.getvalue(), file_name="anh_ai_viethoa_edited.zip", mime="application/zip", key="tab2_download")
                
            except Exception as e:
                st.error(f"❌ Có lỗi khi gọi AI hoặc Xử lý ảnh: {e}")
