#!/usr/bin/env python3

with open('app.py', 'r') as f:
    lines = f.readlines()

print("🔍 Duplicate 'home' functions খোঁজা হচ্ছে...")
print("=" * 50)

home_count = 0
for i, line in enumerate(lines, 1):
    if 'def home' in line or '@app.route("/")' in line:
        home_count += 1
        print(f"লাইন {i}: {line.strip()}")
        # আগের 2 লাইন দেখুন
        if i > 2:
            print(f"  পূর্ববর্তী: {lines[i-2].strip()}")
        print(f"  বর্তমান: {lines[i-1].strip()}")
        # পরের 2 লাইন দেখুন
        if i < len(lines):
            print(f"  পরবর্তী: {lines[i].strip()}")
        print()

print(f"\n✅ মোট {home_count} টি 'home' function পাওয়া গেছে")

if home_count > 1:
    print("\n❌ সমস্যা: একাধিক home function আছে!")
    print("সমাধান: শুধু একটি home function রাখতে হবে")
