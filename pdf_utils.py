import fitz  # pymupdf
from PIL import Image
import pytesseract

def extract_text_from_image(image):
    """
    Use OCR to extract text from a PIL image object.
    """
    text = pytesseract.image_to_string(image)
    return text

def process_pdf(input_pdf_path, product_info_crop_fraction=0.5, confirmation_crop_fraction=0.55):
    """
    Convert PDF pages to images and extract relevant pages using pymupdf (fitz).
    """
    try:
        pdf_document = fitz.open(input_pdf_path)
        num_pages = pdf_document.page_count
        
        if num_pages < 2:
            raise ValueError("The PDF must contain at least 2 pages.")

        # Extract the second page (index 1) and the last page
        product_info_image = convert_pdf_page_to_image(pdf_document, 1)
        confirmation_image = convert_pdf_page_to_image(pdf_document, num_pages - 1)
        
        # Crop the images using the specified parameters
        product_info_image = crop_image(product_info_image, product_info_crop_fraction)
        confirmation_image = crop_image(confirmation_image, confirmation_crop_fraction)
        
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {e}")
    
    return product_info_image, confirmation_image

def convert_pdf_page_to_image(pdf_document, page_number, zoom_factor=3.0):
    """
    Convert a specific PDF page to an image using pymupdf with a specified zoom factor.
    """
    page = pdf_document.load_page(page_number)
    
    # Set the zoom factor for higher resolution
    matrix = fitz.Matrix(zoom_factor, zoom_factor)  # (x_scale, y_scale)
    pix = page.get_pixmap(matrix=matrix)
    
    # Convert Pixmap to PIL Image
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return image

def crop_image(image, top_fraction):
    """
    Crop the image based on the top_fraction parameter.
    """
    width, height = image.size
    top_height = int(height * top_fraction)  # Ensure this is an integer
    cropped_image = image.crop((0, 0, width, top_height))
    return cropped_image
