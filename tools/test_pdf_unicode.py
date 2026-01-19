from xhtml2pdf import pisa
import os

def test_unicode_pdf():
    # Define HTML with Font Face
    # Windows native emoji font
    font_path = "C:/Windows/Fonts/seguiemj.ttf"
    
    html_content = f"""
    <html>
    <head>
        <style>
            @font-face {{
                font-family: 'Segoe UI Emoji';
                src: url('{font_path}');
            }}
            body {{
                font-family: 'Segoe UI Emoji', sans-serif;
                font-size: 20px;
            }}
            .emoji {{
                font-family: 'Segoe UI Emoji';
            }}
        </style>
    </head>
    <body>
        <p>Testing Unicode: 🚀 🎉 🐍 ❤️</p>
        <p>Separate spans: 
           <span class="emoji">🚀</span> 
           <span class="emoji">🎉</span>
        </p>
    </body>
    </html>
    """
    
    output_filename = "test_unicode.pdf"
    
    try:
        with open(output_filename, "wb") as f_out:
            pisa_status = pisa.CreatePDF(html_content, dest=f_out)
            
        if pisa_status.err:
            print("PDF Gen Failed")
        else:
            print(f"PDF Gen Success: {output_filename}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_unicode_pdf()
