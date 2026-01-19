from pypdf import PdfReader
import sys

def analyze_pdf(path):
    try:
        reader = PdfReader(path)
        print(f"Analysis of: {path}")
        print(f"Pages: {len(reader.pages)}")
        
        for i, page in enumerate(reader.pages):
            print(f"-- Page {i+1} --")
            # Extract text
            text = page.extract_text()
            print("Text content abstract:")
            print(text[:500] + "..." if len(text) > 500 else text)
            
            # Try to get font info/resources
            if '/Resources' in page:
                resources = page['/Resources']
                # Dereference if needed
                if hasattr(resources, 'get_object'):
                     resources = resources.get_object()
                     
                print(f"Resources Keys: {list(resources.keys())}")
                
                if '/Font' in resources:
                    fonts = resources['/Font']
                    print("\nFonts used on page:")
                    for font_name in fonts:
                        # font_obj = fonts[font_name].get_object()
                        print(f" - {font_name}")
                
                if '/XObject' in resources:
                    xobjects = resources['/XObject']
                    print("\nXObjects (Images/Forms) on page:")
                    for obj_name in xobjects:
                        obj = xobjects[obj_name]  # .get_object() if needed? pypdf lazy loads
                        try:
                            # Dereference indirect object
                            if hasattr(obj, 'get_object'):
                                obj = obj.get_object()
                                
                            subtype = obj.get('/Subtype')
                            if subtype == '/Image':
                                width = obj.get('/Width')
                                height = obj.get('/Height')
                                print(f" - Image {obj_name}: {width}x{height} px")
                            else:
                                print(f" - XObject {obj_name}: {subtype}")
                        except Exception as e:
                            print(f" - Error interpreting {obj_name}: {e}")

                        
        print("\nDone.")
    except Exception as e:
        print(f"Error analyzing PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_pdf(sys.argv[1])
    else:
        print("Usage: python tools/debug_pdf.py <path_to_pdf>")
