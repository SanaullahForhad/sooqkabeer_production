import re

with open('app.py', 'r') as f:
    content = f.read()

# products রুট আছে কিনা চেক
if 'def products' in content:
    # products রুটের পরেই shop রুট যোগ
    content = re.sub(
        r'(def products\(.*?\):.*?\n)',
        r'\1\n\n@app.route(\'/shop\')\ndef shop():\n    return products()\n',
        content,
        flags=re.DOTALL
    )
    
    with open('app.py', 'w') as f:
        f.write(content)
    print("✅ Added shop route that redirects to products")
else:
    print("❌ products route not found")
