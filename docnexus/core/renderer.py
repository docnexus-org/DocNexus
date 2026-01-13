from typing import List, Callable
import markdown
import re
import pymdownx.superfences
import pymdownx.emoji
import pymdownx.saneheaders
# pymdownx.smarty removed (deprecated in v10)
import pymdownx.critic
import pymdownx.magiclink
import pymdownx.tasklist
import markdown.extensions.meta
import markdown.extensions.wikilinks
import logging
# Explicit imports to force PyInstaller detection and runtime availability
import markdown.extensions.wikilinks
import markdown.extensions.smarty
import markdown.extensions.admonition
import markdown.extensions.meta
import markdown.extensions.toc
import markdown.extensions.fenced_code
import markdown.extensions.tables
import markdown.extensions.codehilite

logger = logging.getLogger(__name__)

# Baseline/standard rendering: just Markdown -> HTML with extensions

def render_github_alerts(md_text: str) -> str:
# ... (rest of function same, just sync context)
    """
    Convert GitHub-style alerts to Python-Markdown Admonition syntax.
    > [!NOTE] 
    > Content
    
    Becomes:
    !!! note
        Content
    """
    # Regex to match the start of the blockquote with the alert tag
    # Captures: 1=Type, 2=Remaining content on that line
    pattern = r'^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$'
    
    def replacer(match):
        alert_type = match.group(1).lower()
        content = match.group(2)
        # Map GitHub types to Admonition types if necessary (Standard are mostly same)
        # GitHub: NOTE, TIP, IMPORTANT, WARNING, CAUTION
        # Admonition: note, tip, important, warning, caution (standard mapping works)
        return f'!!! {alert_type} "{alert_type.title()}"\n    {content}'

    # Iterate line by line to handle nested blockquotes properly logic is complex for regex 
    # naive replacement on the specific line is usually sufficient for simple cases.
    # We must ensure we don't break the blockquote structure for subsequent lines.
    # The standard admonition extension expects indented content for the body.
    # GitHub uses '>' for the whole block.
    # So we essentially need to convert the whole '>' block into an indented block.
    
    # Simple multi-line regex approach:
    # 1. Find the header line `> [!NOTE] ...`
    # 2. Convert it to `!!! note "Note"`
    # 3. Subsequent lines starting with `>` need to be indented instead of `>`.
    
    # For robust implementation without a full parser, we'll strip the leading `> ` 
    # from the immediate lines following an alert tag.
    
    lines = md_text.split('\n')
    out_lines = []
    in_alert = False
    
    for line in lines:
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            alert_type = match.group(1).lower()
            remainder = match.group(2)
            out_lines.append(f'!!! {alert_type}')
            if remainder.strip():
                out_lines.append(f'    {remainder}')
            in_alert = True
        elif in_alert and line.strip().startswith('>'):
            # This is a continuation of the alert block
            # Strip the '>' and indentation
            content = re.sub(r'^>\s?', '', line)
            out_lines.append(f'    {content}')
        elif in_alert and not line.strip():
             # Empty line inside/after alert, keep it indented to be safe or break?
             # Standard admonitions end on double newline. 
             out_lines.append('')
        else:
            # Normal line, breaks the alert context if it was active and not empty
            if in_alert and line.strip():
                in_alert = False
            out_lines.append(line)
            
    return '\n'.join(out_lines)



# Patch standard WikiLinkExtension to allow dots in filenames (e.g. [[v1.2.6]])
from markdown.extensions.wikilinks import WikiLinkExtension, WikiLinksInlineProcessor

class EnhancedWikiLinkExtension(WikiLinkExtension):
    def extendMarkdown(self, md):
        self.md = md
        # Regex to match [[WikiLink]] including dots and standard chars
        # Original: \[\[([\w0-9_ -]+)\]\]
        WIKILINK_RE = r'\[\[([\w0-9_ \-\.]+)\]\]'
        config = self.getConfigs()
        wikilinkPattern = WikiLinksInlineProcessor(WIKILINK_RE, config)
        wikilinkPattern.md = md
        md.inlinePatterns.register(wikilinkPattern, 'wikilink', 75)

def render_baseline(md_text: str) -> str:
    # 1. Remove [TOC] marker
    md_text = re.sub(r'^\[TOC\]$', '', md_text, flags=re.MULTILINE | re.IGNORECASE)

    # 2. Remove legacy TOC placeholders
    md_text = re.sub(r'<!--TOC_PLACEHOLDER_START-->.*?<!--TOC_PLACEHOLDER_END-->', '', md_text, flags=re.DOTALL)
    
    # 3. Pre-process GitHub Alerts
    md_text = render_github_alerts(md_text)
    
    # Render markdown to HTML
    md_instance = markdown.Markdown(
        extensions=[
            'markdown.extensions.meta',       # Metadata / Frontmatter
            # 'markdown.extensions.wikilinks', # Replaced by EnhancedWikiLinkExtension below
            'fenced_code',
            'tables',
            'nl2br',
            'sane_lists',
            'codehilite',
            'toc',
            'extra',
            'attr_list',
            'def_list',
            'abbr',
            'footnotes',
            'md_in_html',
            'admonition',
            'pymdownx.arithmatex',
            'pymdownx.betterem',
            'pymdownx.caret',
            'pymdownx.mark',
            'pymdownx.tilde',
            'pymdownx.details',
            'pymdownx.highlight',
            'pymdownx.inlinehilite',
            'pymdownx.keys',
            'pymdownx.smartsymbols',
            'pymdownx.snippets',
            'pymdownx.superfences',
            'pymdownx.tabbed',
            'pymdownx.tasklist',
            'pymdownx.magiclink',
            'pymdownx.emoji',                 # Emojis :smile:
            'pymdownx.saneheaders',           # Stable headers
            # 'pymdownx.smarty',              # Removed (Deprecated)
            'markdown.extensions.smarty',     # Standard Smarty (Quotes/Dashes)
            'pymdownx.critic',                # CriticMarkup {++ ++}
            EnhancedWikiLinkExtension(base_url='/file/', end_url='') # Custom Extension Instance
        ],
        extension_configs={
            "pymdownx.arithmatex": {
                "generic": True,
            },
            "pymdownx.caret": {
                "insert": True,
            },
            "pymdownx.superfences": {
                "custom_fences": [
                    {
                        'name': 'mermaid',
                        'class': 'mermaid',
                        'format': pymdownx.superfences.fence_div_format
                    }
                ]
            },
            "pymdownx.emoji": {
                "emoji_index": pymdownx.emoji.gemoji,
                "emoji_generator": pymdownx.emoji.to_svg,
            } 
        }
    )
    
    
    # Custom Inline Patterns
    # ++Insert++ -> <ins>Insert</ins>
    from markdown.inlinepatterns import SimpleTagPattern
    INS_PATTERN = r'(\+\+)(.+?)(\+\+)'
    md_instance.inlinePatterns.register(SimpleTagPattern(INS_PATTERN, 'ins'), 'ins', 175)

    logger.debug(f"Render baseline: {len(md_text)} chars input")
    html_output = md_instance.convert(md_text)
    
    # Return both HTML (clean of TOC) and the TOC generated by python-markdown
    return html_output, md_instance.toc


def run_pipeline(md_text: str, steps: List[Callable[[str], str]]) -> str:
    out = md_text
    logger.debug(f"Running pipeline with {len(steps)} steps")
    for fn in steps:
        out = fn(out)
    return out
