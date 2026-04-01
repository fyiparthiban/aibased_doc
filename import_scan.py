import os
import ast

root = os.getcwd()
imports = set()
for dirpath, dirnames, filenames in os.walk(root):
    if any(part in ('venv', '.venv', '__pycache__', '.git') for part in dirpath.replace('\\', '/').split('/')):
        continue
    for fn in filenames:
        if fn.endswith('.py'):
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=path)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.add(n.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split('.')[0])

for name in sorted(imports):
    print(name)
