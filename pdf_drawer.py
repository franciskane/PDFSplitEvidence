import os
import tempfile
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image
from pdf_utils import process_pdf, crop_image
import re

def sanitize_filename(filename):
    """
    Sanitize the filename for safe usage in file paths by removing/replacing characters that
    are not allowed by the filesystem, but preserving valid Unicode characters.
    """
    # Remove or replace invalid characters (for file systems like Windows, etc.)
    return re.sub(r'[\/:*?"<>|]', '_', filename)

def draw_rectangle_with_images(product_info_image, confirmation_image, output_pdf_path, title):
    # Create temporary files for images
    temp_image_path1 = tempfile.mktemp(suffix=".png")
    temp_image_path2 = tempfile.mktemp(suffix=".png")

    # Define page size and margins
    page_width, page_height = map(int, A4)
    outer_margin = int(0.8 * inch)
    title_height = int((page_height - 2 * outer_margin) / 36)
    rectangle_width = int(page_width - 2 * outer_margin)
    rectangle_height = int(page_height - 2 * outer_margin)
    content_height = rectangle_height - title_height
    content_section_height = int(content_height / 2)
    
    # Title settings
    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    c.setFont("Helvetica", 12)  # Use default font
    
    # Calculate title position
    title_x = page_width / 2
    title_y = page_height - outer_margin - title_height
    
    # Draw the main rectangle (this includes the title area)
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(
        outer_margin, 
        outer_margin, 
        rectangle_width, 
        rectangle_height, 
        stroke=True, 
        fill=False
    )
    
    # Draw the line to separate the title from the content area
    divider_y = page_height - outer_margin - title_height
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.line(
        outer_margin, 
        divider_y,
        page_width - outer_margin, 
        divider_y
    )
    
    # Draw the title text centered horizontally and adjusted within the title area
    c.drawCentredString(title_x, title_y + title_height * 0.3, title)
    
    # Draw the line to separate the content sections
    content_divider_y = divider_y - content_section_height
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.line(
        outer_margin, 
        content_divider_y,
        page_width - outer_margin, 
        content_divider_y
    )

    # Save images to temporary files
    product_info_image.save(temp_image_path1)
    confirmation_image.save(temp_image_path2)

    # Debugging: Print temporary file paths and check if they exist
    print(f"Temporary image path 1: {temp_image_path1}, Exists: {os.path.exists(temp_image_path1)}")
    print(f"Temporary image path 2: {temp_image_path2}, Exists: {os.path.exists(temp_image_path2)}")

    # Check image sizes
    with Image.open(temp_image_path1) as img:
        print(f"Product info image size: {img.size}")
    with Image.open(temp_image_path2) as img:
        print(f"Confirmation image size: {img.size}")

    # Draw the images inside the content area
    c.drawImage(
        temp_image_path1, 
        outer_margin, 
        content_divider_y,
        width=rectangle_width, 
        height=content_section_height, 
        preserveAspectRatio=False
    )
    c.drawImage(
        temp_image_path2, 
        outer_margin, 
        outer_margin,
        width=rectangle_width, 
        height=content_section_height, 
        preserveAspectRatio=False
    )
    
    # Save the PDF
    c.save()

    # Clean up temporary files
    os.remove(temp_image_path1)
    os.remove(temp_image_path2)

def compile_pdf(input_pdf_path, output_pdf_path):
    """
    Full process to compile the PDF from the input.
    """
    product_info_image, confirmation_image = process_pdf(input_pdf_path)
    
    if not isinstance(product_info_image, Image.Image) or not isinstance(confirmation_image, Image.Image):
        raise ValueError("Extracted images are not valid PIL images.")
    
    cropped_product_info = crop_image(product_info_image, top_fraction=0.5)
    cropped_confirmation = crop_image(confirmation_image, top_fraction=0.5)
    
    # Get the base filename and sanitize it for safe usage
    base_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]
    sanitized_filename = sanitize_filename(base_filename)

    # Pass the sanitized filename to be used as title
    draw_rectangle_with_images(
        cropped_product_info, cropped_confirmation, output_pdf_path, title=sanitized_filename
    )
