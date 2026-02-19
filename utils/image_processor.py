from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

class ImageProcessor:
    @staticmethod
    def apply_blur(image, box):
        """
        Applies blur to a specific region (box: (x1, y1, x2, y2)).
        """
        region = image.crop(box)
        blurred_region = region.filter(ImageFilter.GaussianBlur(radius=10))
        image.paste(blurred_region, box)
        return image

    @staticmethod
    def add_watermark(image, text, timestamp=True):
        """
        Adds a watermark text and/or timestamp to the bottom right.
        """
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        from datetime import datetime
        if timestamp:
            text = f"{text} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            
        # Standard way to get text size in newer Pillow versions
        bbox = draw.textbbox((0, 0), text, font=font)
        textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        margin = 10
        x = width - textwidth - margin
        y = height - textheight - margin
        
        # Draw background for readability
        draw.rectangle([x-5, y-5, width, height], fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        return image

    @staticmethod
    def draw_annotation(image, shape_type, start_point, end_point, color=(255, 0, 0), width=3, text="", points=None):
        """
        Draws a shape (rect, arrow, line, text, pen) on the image.
        """
        draw = ImageDraw.Draw(image)
        if shape_type == "rect":
            draw.rectangle([start_point, end_point], outline=color, width=width)
        elif shape_type == "line":
            draw.line([start_point, end_point], fill=color, width=width)
        elif shape_type == "pen" and points:
            draw.line(points, fill=color, width=width, joint="curve")
        elif shape_type == "arrow":
            # Basic arrow: line + triangle
            draw.line([start_point, end_point], fill=color, width=width)
            # Arrowhead calculation (simplified)
            import math
            angle = math.atan2(end_point[1] - start_point[1], end_point[0] - start_point[0])
            arrow_len = 15
            p1 = (end_point[0] - arrow_len * math.cos(angle - math.pi/6), 
                  end_point[1] - arrow_len * math.sin(angle - math.pi/6))
            p2 = (end_point[0] - arrow_len * math.cos(angle + math.pi/6), 
                  end_point[1] - arrow_len * math.sin(angle + math.pi/6))
            draw.polygon([end_point, p1, p2], fill=color)
        elif shape_type == "text" and text:
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except IOError:
                font = ImageFont.load_default()
            draw.text(start_point, text, font=font, fill=color)
        return image
