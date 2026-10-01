#!/usr/bin/env python3
"""Fail CI if MVC controller bytecode loses Java parameter names."""

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CLASSES = ROOT / "ruoyi-admin" / "target" / "classes"
SENTINELS = {
    "com.ruoyi.web.controller.monitor.SysUserOnlineController": ("ipaddr", "userName"),
    "com.ruoyi.web.controller.system.SysConfigController": ("configId",),
    "com.ruoyi.web.controller.system.SysDeptController": ("deptId",),
    "com.ruoyi.web.controller.system.SysRoleController": ("roleId",),
}


def main() -> int:
    if not CLASSES.is_dir():
        print(f"Compiled admin classes are missing: {CLASSES}", file=sys.stderr)
        return 2
    for class_name, names in SENTINELS.items():
        result = subprocess.run(
            ["javap", "-v", "-classpath", str(CLASSES), class_name],
            capture_output=True, text=True, check=False,
        )
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            return 2
        parameter_blocks = re.findall(
            r"(?m)^    MethodParameters:\n      Name\s+Flags\n((?:      .*\n)+)",
            result.stdout,
        )
        observed = {
            line.strip().split()[0]
            for block in parameter_blocks
            for line in block.splitlines()
            if line.strip()
        }
        missing = set(names) - observed
        if missing:
            print(f"{class_name} lacks bytecode parameter names: {sorted(missing)}", file=sys.stderr)
            return 1
    print(f"MVC parameter metadata verified for {len(SENTINELS)} compiled controllers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
