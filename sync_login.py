import sys

def patch():
    with open('app.py', 'r') as f:
        lines = f.readlines()

    new_lines = []
    in_login = False
    for line in lines:
        if 'def vendor_login():' in line or 'def login():' in line:
            in_login = True
        
        # নতুন ডিজাইনে সাধারণত 'email' বা 'identifier' থাকে
        # আমরা নিশ্চিত করছি যেন এটি 'email' এবং 'password' পায়
        if in_login and "request.form.get('email')" in line:
            line = line.replace("request.form.get('email')", "request.form.get('email', request.form.get('identifier'))")
        
        new_lines.append(line)
        if in_login and 'return render_template' in line:
            in_login = False

    with open('app.py', 'w') as f:
        f.writelines(new_lines)
    print("=== Login Logic Synced with New Design! (HKO-001) ===")

if __name__ == "__main__":
    patch()
