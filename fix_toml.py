import re
import ast

with open("pyproject.toml", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("[[project.authors]]"):
        if len(new_lines) > 0 and new_lines[-1].strip() != "":
            new_lines.append("\n")
        new_lines.append(line)
        continue

    # Look for inline arrays
    match = re.search(r'^([a-zA-Z0-9_\-]+)\s*=\s*\[(.*)\]\s*$', line.strip())
    if match:
        key = match.group(1)
        items_str = match.group(2)
        if items_str.strip() == "":
            new_lines.append(line)
        else:
            try:
                # ast.literal_eval might not like trailing comma before closing bracket if it was parsed as string
                # Wait, ast.literal_eval("[1,2,]") works in Python.
                items = ast.literal_eval(f"[{items_str}]")
                new_lines.append(f"{key} = [\n")
                for item in items:
                    if isinstance(item, str):
                        new_lines.append(f'    "{item}",\n')
                    else:
                        new_lines.append(f'    {item},\n')
                new_lines.append("]\n")
            except Exception as e:
                new_lines.append(line)
    else:
        new_lines.append(line)

with open("pyproject.toml", "w") as f:
    f.writelines(new_lines)
