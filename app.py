import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile

# Cấu hình chuẩn 9:16
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

st.set_page_config(page_title="Bot Tạo Ảnh Dọc", page_icon="📱")
st.title("📱 Tool Tạo Ảnh Dọc 9:16 Tự Động")
st.markdown("Kéo thả ảnh cần xử lý vào bên dưới. Hệ thống sẽ tự động thêm viền mờ và resize về chuẩn 1080x1920.")

# Khung upload file
uploaded_files = st.file_uploader("Chọn ảnh hoặc kéo thả vào đây (Hỗ trợ nhiều ảnh)", 
                                  accept_multiple_files=True, 
                                  type=['png', 'jpg', 'jpeg', 'webp'])

if uploaded_files:
    if st.button("🚀 Bắt Đầu Xử Lý", type="primary"):
        # Tạo file ZIP trong bộ nhớ để chứa các ảnh đã xử lý
        zip_buffer = io.BytesIO()
        
        # Thanh tiến trình hiển thị cho trực quan
        progress_bar = st.progress(0)
        total_files = len(uploaded_files)
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, file in enumerate(uploaded_files):
                try:
                    # 1. Đọc ảnh
                    img = Image.open(file).convert("RGB")
                    img_w, img_h = img.size

                    # 2. Tạo nền mờ
                    bg_ratio = max(TARGET_WIDTH / img_w, TARGET_HEIGHT / img_h)
                    bg_new_w = int(img_w * bg_ratio)
                    bg_new_h = int(img_h * bg_ratio)
                    
                    bg_img = img.resize((bg_new_w, bg_new_h), Image.Resampling.LANCZOS)
                    
                    left = (bg_new_w - TARGET_WIDTH) / 2
                    top = (bg_new_h - TARGET_HEIGHT) / 2
                    bg_img = bg_img.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))
                    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=30))

                    # 3. Xử lý ảnh chính
                    fg_ratio = min(TARGET_WIDTH / img_w, TARGET_HEIGHT / img_h)
                    fg_new_w = int(img_w * fg_ratio)
                    fg_new_h = int(img_h * fg_ratio)
                    
                    fg_img = img.resize((fg_new_w, fg_new_h), Image.Resampling.LANCZOS)

                    # 4. Dán ảnh
                    offset_x = (TARGET_WIDTH - fg_new_w) // 2
                    offset_y = (TARGET_HEIGHT - fg_new_h) // 2
                    bg_img.paste(fg_img, (offset_x, offset_y))

                    # 5. Lưu ảnh vào bộ nhớ ảo thay vì lưu xuống ổ cứng
                    img_byte_arr = io.BytesIO()
                    bg_img.save(img_byte_arr, format='JPEG', quality=95)
                    
                    # 6. Ghi vào file ZIP
                    zip_file.writestr(f"916_{file.name}", img_byte_arr.getvalue())
                    
                    # Cập nhật thanh tiến trình
                    progress_bar.progress((i + 1) / total_files)
                    
                except Exception as e:
                    st.error(f"Lỗi file {file.name}: {e}")

        st.success("🎉 Đã xử lý xong toàn bộ ảnh!")
        
        # Nút tải xuống file ZIP
        st.download_button(
            label="📦 Tải tất cả ảnh về (.zip)",
            data=zip_buffer.getvalue(),
            file_name="anh_doc_916.zip",
            mime="application/zip"
        )