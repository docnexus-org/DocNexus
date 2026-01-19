import markdown
from bs4 import BeautifulSoup

def test_footnote_html():
    md_text = """
This is a paragraph with a footnote[^1] and another[^2].

[^1]: This is the first footnote.
[^2]: This is the second footnote.
"""
    
    html = markdown.markdown(md_text, extensions=['footnotes'])
    
    print("--- Generated HTML ---")
    print(html)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Analyze References
    refs = soup.find_all('sup', id=lambda x: x and x.startswith('fnref'))
    print(f"\nFound {len(refs)} references.")
    for ref in refs:
        a = ref.find('a')
        print(f"Ref: {ref}, Link: {a['href'] if a else 'None'}")
        
    # Analyze Footnote Section
    div = soup.find('div', class_='footnote')
    if div:
        print(f"\nFootnote Section Found. Classes: {div.get('class')}")
        items = div.find_all('li')
        print(f"Items: {len(items)}")
        for item in items:
            print(f"Item: {item.get_text().strip()}")
            backlink = item.find('a', class_='footnote-backref')
            print(f"Backlink: {backlink['href'] if backlink else 'None'}")
    else:
        print("\nNo Footnote Section Found.")

if __name__ == "__main__":
    test_footnote_html()
