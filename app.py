import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile

st.set_page_config(page_title="Bot Tạo Ảnh Tự Động", page_icon="📱")
st.title("📱 Tool Xử Lý Ảnh Tự Động")

st.markdown("💡 **Mẹo:** Bạn có thể bôi đen nhiều ảnh trong máy tính và **Kéo Thả** thẳng vào khung bên dưới để xử lý hàng loạt cho nhanh nhé!")

# Menu thả xuống chọn tỷ lệ
ratio_choice = st.selectbox(
    "📐 Chọn định dạng ảnh đầu ra:", 
    [
        "9:16 (Chuẩn Video dọc: TikTok, Shorts, Reels)", 
        "1:1 (Chuẩn Ảnh vuông: Sản phẩm Shopee, Print-on-Demand)"
    ]
)

# Thiết lập kích thước chuẩn dựa trên lựa chọn của người dùng
if ratio_choice.startswith("9:16"):
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    file_prefix = "916_"
else:
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1080
    file_prefix = "11_"

# Khung upload file
uploaded_files = st.file_uploader(
    "Chọn ảnh hoặc Kéo thả ảnh trực tiếp vào đây", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg', 'webp']
)

if uploaded_files:
    if st.button("🚀 Bắt Đầu Xử Lý", type="primary"):
        zip_buffer = io.BytesIO()
        
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

                    # 5. Lưu ảnh vào bộ nhớ ảo
                    img_byte_arr = io.BytesIO()
                    bg_img.save(img_byte_arr, format='JPEG', quality=95)
                    
                    # 6. Ghi vào file ZIP với tiền tố tương ứng (916_ hoặc 11_)
                    file_name = file.name if file.name else f"pasted_image_{i}.jpg"
                    zip_file.writestr(f"{file_prefix}{file_name}", img_byte_arr.getvalue())
                    
                    # Cập nhật thanh tiến trình
                    progress_bar.progress((i + 1) / total_files)
                    
                except Exception as e:
                    st.error(f"Lỗi file {file.name}: {e}")

        st.success("🎉 Đã xử lý xong toàn bộ ảnh!")
        
        # Nút tải xuống file ZIP
        st.download_button(
            label="📦 Tải tất cả ảnh về (.zip)",
            data=zip_buffer.getvalue(),
            file_name=f"anh_xuly_{file_prefix[:-1]}.zip",
            mime="application/zip"
        )