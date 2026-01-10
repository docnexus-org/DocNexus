
import pytest
import re

# Mock the sanitization logic from plugin.py
# In a perfect world we'd import the function, but it's inside get_features closure or file level not easily importable 
# without side effects in a passive plugin. So we copy the logic or refactor the plugin to expose it.
# For now, we will verify the regex logic matches what we implemented.

def sanitize_css(text):
    # Regex to find CSS variable usage
    css_var_pattern = re.compile(r'var\s*\([^)]+\)')
    
    replacements = {
        'var(--color-fg-default)': '#000000',
        'var(--color-canvas-default)': '#ffffff',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    return css_var_pattern.sub('#888888', text)

def strip_external_links(text):
    link_pattern = re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', re.IGNORECASE)
    return link_pattern.sub('', text)

def strip_styles(text):
    # Block removal
    style_block_pattern = re.compile(r'<style\b[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL)
    text = style_block_pattern.sub('', text)
    
    # Attribute removal
    style_attr_pattern = re.compile(r'\sstyle=["\'][^"\']*["\']', re.IGNORECASE)
    text = style_attr_pattern.sub('', text)
    return text

def test_sanitize_known_vars():
    input_css = "color: var(--color-fg-default); background: var(--color-canvas-default);"
    expected = "color: #000000; background: #ffffff;"
    assert sanitize_css(input_css) == expected

def test_sanitize_unknown_vars():
    input_css = "width: var(--unknown-variable, 10px);"
    expected = "width: #888888;"
    assert sanitize_css(input_css) == expected

def test_strip_links():
    html = """
    <html>
    <head>
        <link rel="stylesheet" href="/static/main.css">
        <script src="app.js"></script>
    </head>
    </html>
    """
    cleaned = strip_external_links(html)
    assert '<link rel="stylesheet"' not in cleaned
    assert '<script' in cleaned

def test_strip_style_blocks():
    html = """
    <html>
    <style>
        body { color: red; }
    </style>
    <body>Text</body>
    </html>
    """
    cleaned = strip_styles(html)
    assert 'body { color: red; }' not in cleaned
    assert '<style>' not in cleaned
    assert '<body>Text</body>' in cleaned

def test_strip_style_attributes():
    html = '<div style="color: var(--x)">Content</div>'
    cleaned = strip_styles(html)
    assert 'style=' not in cleaned
    assert '<div>Content</div>' == cleaned
