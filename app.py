import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import google.generativeai as genai

st.set_page_config(page_title="Bot Xử Lý Ảnh Pro", page_icon="📱", layout="wide")
st.title("📱 Hệ Thống Xử Lý Ảnh Tự Động")

# Chia giao diện làm 2 Tab
tab1, tab2 = st.tabs(["⚙️ Cắt Ghép Cơ Bản (Tốc độ cao)", "✨ Xử Lý Bằng AI (Nano Banana 2)"])

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
# TAB 2: TOOL XỬ LÝ ẢNH BẰNG AI
# ==========================================
with tab2:
    st.markdown("💡 **Tính năng AI:** Tải ảnh lên và ra lệnh cho AI (Ví dụ: Xóa chữ, đổi nền, dịch sang tiếng Việt, sắp xếp lại bố cục).")
    
    # Ô nhập API Key (Bảo mật, ẩn ký tự)
    api_key_input = st.text_input("🔑 Nhập Gemini API Key của bạn (Lấy miễn phí tại aistudio.google.com):", type="password")
    
    # Khung upload ảnh cho AI
    ai_uploaded_files = st.file_uploader("Tải ảnh cần AI xử lý lên đây", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="tab2_upload")
    
    # Ô nhập lệnh (Prompt)
    ai_prompt = st.text_area("🤖 Lệnh cho AI (Prompt):", placeholder="Ví dụ: Chỉnh sửa ảnh này thành ảnh cho thị trường Việt. Sao cho Text không được nằm ở 1/3 phía trên và dưới...")

    if ai_uploaded_files and ai_prompt and api_key_input:
        if st.button("✨ Bắt Đầu Xử Lý Bằng AI", type="primary", key="tab2_btn"):
            try:
                # Cấu hình API Key
                genai.configure(api_key=api_key_input)
                
                # Gọi mô hình AI (Sử dụng Gemini 1.5 Pro hỗ trợ phân tích và xử lý hình ảnh)
                model = genai.GenerativeModel('gemini-1.5-pro')
                
                st.info("Đang gửi yêu cầu lên máy chủ AI... Quá trình này có thể mất vài chục giây tùy số lượng ảnh.")
                progress_bar_ai = st.progress(0)
                
                # Lưu ý: Code dưới đây giả lập luồng gọi API xử lý ảnh (Image-to-Image editing). 
                # Tùy thuộc vào bản cập nhật API hiện hành của Google, bạn sẽ nhận được response dạng nội dung hướng dẫn 
                # hoặc URL ảnh đầu ra.
                for i, file in enumerate(ai_uploaded_files):
                    img = Image.open(file)
                    
                    # Gửi ảnh và prompt lên AI
                    response = model.generate_content([ai_prompt, img])
                    
                    st.write(f"**Kết quả cho ảnh {file.name}:**")
                    st.write(response.text) # Hiển thị phản hồi từ AI
                    
                    progress_bar_ai.progress((i + 1) / len(ai_uploaded_files))
                    
                st.success("🎉 AI đã xử lý xong!")
                
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra khi gọi AI (Vui lòng kiểm tra lại API Key): {e}")