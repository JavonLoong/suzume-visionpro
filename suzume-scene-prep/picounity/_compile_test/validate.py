# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")

# JSON 验证
try:
    json.load(open("Packages/manifest.json", encoding="utf-8"))
    print("manifest.json: OK (valid JSON)")
except Exception as e:
    print("manifest.json ERROR:", e)

# shader 花括号配对检查
for sh in ["Assets/Shaders/PortalMask.shader", "Assets/Shaders/PortalTarget.shader"]:
    s = open(sh, encoding="utf-8").read()
    bal = s.count("{") - s.count("}")
    paren = s.count("(") - s.count(")")
    status = "OK" if bal == 0 and paren == 0 else "MISMATCH"
    print(f"{sh}: braces={bal} parens={paren} -> {status}")
