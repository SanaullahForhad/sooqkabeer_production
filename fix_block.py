with open('app.py', 'r') as f:
    lines = f.readlines()

# এই লাইনগুলো ঠিক করবো (0-indexed)
lines[1690] = '        ' + lines[1690].lstrip()  # vendor_id
lines[1691] = '        ' + lines[1691].lstrip()  # vendor_code

# নিচের লাইনগুলোও চেক করুন
for i in range(1692, 1700):
    if lines[i].strip():  # খালি লাইন না হলে
        current_indent = len(lines[i]) - len(lines[i].lstrip())
        # যদি 4 বা 8 স্পেস থেকে কম হয়, 8 স্পেসে সেট করুন
        if current_indent < 8:
            lines[i] = '        ' + lines[i].lstrip()

with open('app.py', 'w') as f:
    f.writelines(lines)
print("ব্লকটি ঠিক করা হয়েছে")
