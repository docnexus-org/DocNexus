from bs4 import BeautifulSoup
import sys
import os

# Add parent dir to path to import plugin
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

html_content = """
<div class="markdown-content" id="documentContent">
    <h1>Task List Test</h1>
    <ul class="task-list">
        <li class="task-list-item">
            <input type="checkbox" class="task-list-item-checkbox" disabled> Incomplete Task
        </li>
        <li class="task-list-item">
            <input type="checkbox" class="task-list-item-checkbox" checked disabled> Completed Task
        </li>
        <li class="task-list-item">
            <label>
                <input type="checkbox" class="task-list-item-checkbox" checked disabled> Nested Label Task
            </label>
        </li>
    </ul>
    <p>Ordinary list:</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</div>
"""

soup = BeautifulSoup(html_content, 'html.parser')

print("--- Original HTML ---")
print(soup.prettify())

# Import the transformation logic
# We need to mock the environment or just copy the logic for testing
# For now, let's just inspect what structure we need to transform.
