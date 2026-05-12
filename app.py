import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import zipfile
import urllib.request
import textwrap
import json

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
tab1, tab2 = st.tabs(["⚙️ Cắt Ghép Cơ Bản", "✨ Quét Tọa Độ & Việt Hóa (Miễn Phí 100%)"])

# ==========================================
# TAB 1: TOOL CẮT GHÉP CƠ BẢN NHƯ CŨ
# ==========================================
with tab1:
    st.markdown("💡 **Mẹo:** Kéo thả hàng loạt ảnh vào đây để tự động bo viền mờ theo tỷ lệ.")
    
    ratio_choice = st.selectbox(
        "📐 Chọn định dạng ảnh đầu ra:", 
        ["9:16 (Chuẩn Video dọc)", "1:1 (Chuẩn Ảnh vuông)"],
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
            st.download_button("📦 Tải tất cả ảnh về (.zip)", data=zip_buffer.getvalue(), file_name=f"anh_xuly.zip", mime="application/zip")


# ==========================================
# TAB 2: TOOL AI NHẬN DIỆN TỌA ĐỘ VÀ ĐÈ BOX TRẮNG
# ==========================================
with tab2:
    st.markdown("💡 **Cơ chế hoạt động:** AI quét ảnh, xác định chính xác khu vực chứa chữ gốc. Sau đó Tool tự động vẽ một tấm bảng trắng đè lên khu vực đó và in chữ Tiếng Việt mới vào.")
    
    api_key_input = st.text_input("🔑 Nhập Gemini API Key của bạn:", type="password")
    ai_uploaded_files = st.file_uploader("Tải ảnh chứa text cần dịch", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="tab2_upload")
    
    if ai_uploaded_files and api_key_input:
        if st.button("✨ Quét Vùng Khung & Việt Hóa", type="primary", key="tab2_btn"):
            try:
                client = genai.Client(api_key=api_key_input)
                
                # Dùng model siêu tốc độ và miễn phí
                model_name = 'gemini-2.5-flash'
                st.success(f"✅ Đang kích hoạt radar nhận diện: **{model_name}**")
                
                # Lệnh yêu cầu AI trả về định dạng JSON chứa text và tọa độ
                prompt_text = """Analyze this image. Find the main block of text (like Chinese/foreign promotional text).
                1. Translate the meaning into a very short, catchy Vietnamese hook (maximum 10 words).
                2. Identify the bounding box of that original text block.
                Output ONLY a JSON object with this exact schema:
                {
                    "text": "Vietnamese hook here",
                    "box": [ymin, xmin, ymax, xmax]
                }
                The box coordinates MUST be integers between 0 and 1000 representing the bounding box (ymin=top, xmin=left, ymax=bottom, xmax=right)."""
                
                font_bytes = load_vietnamese_font()
                
                ai_zip_buffer = io.BytesIO()
                progress_bar_ai = st.progress(0)
                total_files = len(ai_uploaded_files)
                
                with zipfile.ZipFile(ai_zip_buffer, "w") as ai_zip_file:
                    for i, file in enumerate(ai_uploaded_files):
                        img = Image.open(file).convert("RGB")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img, caption=f"🖼️ Ảnh Gốc", use_column_width=True)
                        
                        st.write("🔍 AI đang dò tìm tọa độ khung chữ...")
                        
                        # Ép AI trả về chuẩn cấu trúc JSON
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[prompt_text, img],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                            )
                        )
                        
                        try:
                            # Đọc dữ liệu JSON do AI trả về
                            data = json.loads(response.text.strip())
                            vi_text = data.get("text", "SẢN PHẨM HOT")
                            box = data.get("box", [100, 100, 300, 900]) # Fallback nếu lỗi
                            
                            ymin, xmin, ymax, xmax = box
                            
                            # Chuyển đổi tọa độ (tỉ lệ 0-1000) sang Pixel thực tế của ảnh
                            img_w, img_h = img.size
                            top = int((ymin / 1000) * img_h)
                            left = int((xmin / 1000) * img_w)
                            bottom = int((ymax / 1000) * img_h)
                            right = int((xmax / 1000) * img_w)
                            
                            # Mở rộng Box Trắng ra một chút (Padding) để đảm bảo che lấp sạch sẽ 100% chữ cũ
                            padding = 15
                            left = max(0, left - padding)
                            top = max(0, top - padding)
                            right = min(img_w, right + padding)
                            bottom = min(img_h, bottom + padding)
                            
                            # 1. Vẽ Khung Layer Full Trắng
                            draw = ImageDraw.Draw(img)
                            draw.rectangle([left, top, right, bottom], fill=(255, 255, 255))
                            
                            # 2. Xử lý Cỡ Chữ và Tự Động Xuống Dòng để nhét vừa Box Trắng
                            box_width = right - left
                            box_height = bottom - top
                            
                            # Linh hoạt cỡ chữ theo chiều cao của box
                            font_size = max(20, int(box_height * 0.4)) 
                            font = ImageFont.truetype(io.BytesIO(font_bytes), size=font_size)
                            
                            # Tính toán số lượng ký tự trên 1 dòng để không bị tràn khung trắng
                            chars_per_line = max(10, int(box_width / (font_size * 0.5)))
                            wrapper = textwrap.TextWrapper(width=chars_per_line)
                            wrapped_text = wrapper.fill(text=vi_text)
                            
                            # 3. Căn giữa và in Chữ Tiếng Việt (Màu Đen) lên Box Trắng
                            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center')
                            text_w = bbox[2] - bbox[0]
                            text_h = bbox[3] - bbox[1]
                            
                            text_x = left + (box_width - text_w) / 2
                            text_y = top + (box_height - text_h) / 2
                            
                            draw.multiline_text((text_x, text_y), wrapped_text, font=font, fill=(0, 0, 0), align='center')
                            
                            with col2:
                                st.image(img, caption="✨ Đã đè Box Trắng & Việt Hóa", use_column_width=True)
                            
                            # Lưu vào file ZIP
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG', quality=95)
                            file_name = file.name if file.name else f"ai_translated_{i}.jpg"
                            ai_zip_file.writestr(f"AI_BoxTrang_{file_name}", img_byte_arr.getvalue())
                            
                        except Exception as parse_error:
                            st.error(f"❌ Lỗi khi phân tích tọa độ của file này: {parse_error}")
                            
                        progress_bar_ai.progress((i + 1) / total_files)
                
                st.success("🎉 Xong! Toàn bộ ảnh đã được tẩy chữ và Việt Hóa siêu mượt!")
                st.download_button("📦 Tải Ảnh Siêu Tốc Về", data=ai_zip_buffer.getvalue(), file_name="anh_boxtrang_viethoa.zip", mime="application/zip")
                
            except Exception as e:
                st.error(f"❌ Có lỗi kết nối AI: {e}")
