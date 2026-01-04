import re

with open('app.py', 'r') as f:
    lines = f.readlines()

seen = set()
new_lines = []
skip = False

for line in lines:
    # Check for function definition lines
    match = re.search(r'def\s+(login|logout)\(\):', line)
    if match:
        func_name = match.group(1)
        if func_name in seen:
            skip = True  # Duplicate found, start skipping
            continue
        else:
            seen.add(func_name)
            skip = False

    # Stop skipping when we hit a new route decorator
    if line.strip().startswith('@app.route') and skip:
        # Check if this route is for the next function or the same duplicate
        # For simplicity, we keep skip True until a non-duplicate is found
        pass
    
    # We only skip if skip is True and it's not the next legitimate function
    if not skip:
        new_lines.append(line)
    elif line.strip() == "": # Keep empty lines for structure
        new_lines.append(line)
    
    # Reset skip if we hit the end of a block (naive approach)
    if skip and (line.startswith('def ') or line.startswith('@app.route')) and not match:
        # Check if the next function is NOT in seen
        skip = False
        new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)
print("#=== SUCCESS: Duplicate Login/Logout removed! ===#")
