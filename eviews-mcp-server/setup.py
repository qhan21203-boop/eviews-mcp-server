"""
EViews MCP Server - 环境安装脚本
自动下载并配置 32 位 Python 环境
"""
import os
import sys
import zipfile
import urllib.request
import subprocess

PYTHON32_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python32")
PYTHON32_URL = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-win32.zip"
PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


def setup():
    print("=== EViews MCP Server 环境安装 ===\n")

    # 1. Download Python 32-bit
    if os.path.exists(os.path.join(PYTHON32_DIR, "python.exe")):
        print(f"[OK] 32-bit Python 已存在: {PYTHON32_DIR}")
    else:
        print(f"[...] 下载 32-bit Python 到 {PYTHON32_DIR} ...")
        os.makedirs(PYTHON32_DIR, exist_ok=True)
        zip_path = os.path.join(PYTHON32_DIR, "python.zip")
        urllib.request.urlretrieve(PYTHON32_URL, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(PYTHON32_DIR)
        os.remove(zip_path)
        print("[OK] Python 32-bit 安装完成")

    python_exe = os.path.join(PYTHON32_DIR, "python.exe")

    # 2. Enable pip in embeddable Python
    pth_file = os.path.join(PYTHON32_DIR, "python312._pth")
    if os.path.exists(pth_file):
        content = open(pth_file).read()
        if "#import site" in content:
            content = content.replace("#import site", "import site")
            open(pth_file, "w").write(content)
            print("[OK] pip 已启用")

    # 3. Install pip
    print("[...] 安装 pip ...")
    pip_path = os.path.join(PYTHON32_DIR, "get-pip.py")
    urllib.request.urlretrieve(PIP_URL, pip_path)
    subprocess.run([python_exe, pip_path, "--no-warn-script-location"], check=False)
    os.remove(pip_path)

    # 4. Install dependencies
    print("[...] 安装依赖 ...")
    subprocess.run([python_exe, "-m", "pip", "install", "pywin32", "mcp", "--no-warn-script-location"], check=False)

    # 5. Verify
    result = subprocess.run([python_exe, "-c", "import struct; print(struct.calcsize('P')*8)"],
                            capture_output=True, text=True)
    if "32" in result.stdout:
        print(f"\n=== 安装完成！===")
        print(f"32 位 Python: {python_exe}")
    else:
        print("\n[!] 安装可能有问题，请手动检查")


if __name__ == "__main__":
    setup()
