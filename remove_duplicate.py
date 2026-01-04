#!/usr/bin/env python3

with open('app.py', 'r') as f:
    content = f.read()

# সমস্ত লাইন আলাদা করুন
lines = content.split('\n')

# প্রথম home function খুঁজে বের করুন এবং বাকিগুলো রিমুভ করুন
found_first = False
new_lines = []
skip_next_def = False
i = 0

while i < len(lines):
    line = lines[i]
    
    # যদি @app.route("/") পাই
    if '@app.route("/")' in line:
        if not found_first:
            found_first = True
            new_lines.append(line)  # প্রথমটি রাখুন
            print(f"✅ প্রথম home রাউট রাখা হয়েছে (লাইন {i+1})")
        else:
            print(f"❌ ডুপ্লিকেট home রাউট বাদ দেওয়া হচ্ছে (লাইন {i+1})")
            # এই রাউট এবং এর function বাদ দিন
            # পরবর্তী লাইনগুলো যতক্ষণ না অন্য @app.route পাচ্ছি, বাদ দিন
            j = i
            while j < len(lines) and (not lines[j].strip().startswith('@app.route') or '@app.route("/")' in lines[j]):
                print(f"   লাইন {j+1} বাদ: {lines[j].strip()}")
                j += 1
            i = j - 1  # লুপ ইনডেক্স আপডেট
    
    # অন্য সব লাইন যোগ করুন
    elif not skip_next_def or 'def home' not in line:
        new_lines.append(line)
    
    i += 1

# নতুন কন্টেন্ট তৈরি
new_content = '\n'.join(new_lines)

# ফাইল সেভ করুন
with open('app.py', 'w') as f:
    f.write(new_content)

print("\n✅ Duplicate home রাউট রিমুভ করা হয়েছে")
print(f"মোট লাইন: {len(lines)} → {len(new_lines)}")
