import re

def clean_app_py():
    with open('app.py', 'r') as f:
        lines = f.readlines()

    # List of admin functions to check for duplicates
    target_functions = ['admin_dashboard', 'admin_orders', 'admin_vendors', 'admin_users', 'admin_products', 'admin_commissions', 'admin_redirect']
    seen_functions = set()
    new_lines = []
    skip_until_next_route = False

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if line contains a function definition
        func_match = re.search(r'def\s+(\w+)\(\):', line)
        
        if func_match:
            func_name = func_match.group(1)
            if func_name in target_functions:
                if func_name in seen_functions:
                    # We already have this function, skip this one and its content
                    skip_until_next_route = True
                    i += 1
                    continue
                else:
                    seen_functions.add(func_name)
                    skip_until_next_route = False
        
        # If we encounter a new route, we stop skipping (unless it's the next duplicate)
        if line.strip().startswith('@app.route'):
            # Look ahead to see what function this route belongs to
            next_func_name = None
            for j in range(i+1, min(i+5, len(lines))):
                m = re.search(r'def\s+(\w+)\(\):', lines[j])
                if m:
                    next_func_name = m.group(1)
                    break
            
            if next_func_name in seen_functions:
                skip_until_next_route = True
            else:
                skip_until_next_route = False

        if not skip_until_next_route:
            new_lines.append(line)
        
        i += 1

    with open('app.py', 'w') as f:
        f.writelines(new_lines)

clean_app_py()
print("#=== SUCCESS: All duplicate admin functions have been removed! ===#")
