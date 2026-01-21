#!/usr/bin/env python3
# ইন্ডেন্টেশন ফিক্স করার স্ক্রিপ্ট

with open('app.py', 'r') as f:
    lines = f.readlines()

# লাইন 1078 এর ইন্ডেন্টেশন চেক করুন
print("Line 1078 before fix:")
print(repr(lines[1077]))

# ইন্ডেন্টেশন ঠিক করুন (4 স্পেস/ট্যাব)
lines[1077] = '        user_referral_code = generate_referral_code(username)\n'

print("\nLine 1078 after fix:")
print(repr(lines[1077]))

# ফাইল সেভ করুন
with open('app.py', 'w') as f:
    f.writelines(lines)

print("\nIndentation fixed!")
