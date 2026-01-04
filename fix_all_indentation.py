import re

with open('app.py', 'r') as f:
    lines = f.readlines()

# Track indentation levels
indent_stack = [0]  # Start with 0 indentation
current_indent = 0

for i in range(len(lines)):
    line = lines[i]
    stripped = line.lstrip()
    
    # Calculate current indentation
    if stripped:
        current_indent = len(line) - len(stripped)
    else:
        current_indent = 0
    
    # Check for keywords that increase indentation
    if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except ', 'finally:', 'with ')):
        if stripped.endswith(':'):
            # This line should have proper indentation
            expected_indent = indent_stack[-1]
            if current_indent != expected_indent:
                lines[i] = ' ' * expected_indent + stripped
            
            # Next line should be indented more
            indent_stack.append(expected_indent + 4)
    
    # Check for dedent (end of block)
    elif current_indent < indent_stack[-1]:
        while indent_stack and current_indent < indent_stack[-1]:
            indent_stack.pop()
    
    # Fix current line indentation
    if stripped and current_indent != indent_stack[-1]:
        lines[i] = ' ' * indent_stack[-1] + stripped

with open('app.py', 'w') as f:
    f.writelines(lines)

print('✅ Fixed all indentation')
