# ফাইল পড়ি
with open('app.py', 'r') as f:
    lines = f.readlines()

# 1210-1225 লাইনগুলো ঠিক করি (0-ইন্ডেক্সে 1209-1224)
# সমস্যার লাইনগুলো:
# 1213: try:
# 1214: cursor.execute('''
# 1215: connection.commit()
# এইগুলো ভুল

# সঠিক কোড:
correct_lines = [
    "    VALUES (?, ?, ?, ?, ?)\n",
    "    ''', (referrer_id, bonus_amount, 1.0, 'referral_bonus', f'Welcome bonus for referring {username}'))\n",
    "\n",
    "try:\n",
    "    cursor.execute('''\n",
    "    ''')\n",
    "\n",
    "    connection.commit()\n",
    "except Exception as e:\n",
    "    print(f\"Database error: {e}\")\n",
    "    connection.rollback()\n",
    "finally:\n",
    "    pass\n"
]

# 1209 থেকে 1224 পর্যন্ত লাইন রিপ্লেস করি
lines[1209:1225] = correct_lines

# সেভ করি
with open('app_direct_fixed.py', 'w') as f:
    f.writelines(lines)

print("Fixed and saved as app_direct_fixed.py")
