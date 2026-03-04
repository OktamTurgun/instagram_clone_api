import os
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def optimize_image(image_field, max_width=1080, quality=85):
    """
    Rasmni o'lchamini kichraytiradi va WebP formatiga o'tkazadi.
    """
    img = Image.open(image_field)
    
    # RGB formatga o'tkazish (PNG yoki boshqa formatlar uchun)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # O'lchamni proporsional kichraytirish
    if img.width > max_width:
        output_size = (max_width, int((max_width / img.width) * img.height))
        img = img.resize(output_size, Image.LANCZOS)
    
    # Rasmni xotirada (buffer) saqlash
    buffer = BytesIO()
    img.save(buffer, format="WEBP", quality=quality)
    buffer.seek(0)
    
    # Yangi fayl nomini yaratish
    filename = os.path.splitext(image_field.name)[0] + ".webp"
    
    return ContentFile(buffer.read(), name=filename)