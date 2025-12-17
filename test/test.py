import subprocess
import sys
import os
from playwright.sync_api import sync_playwright

def ensure_playwright_installed():
    """确保 Playwright 及其浏览器依赖已正确安装"""
    try:
        # 尝试创建一个 Playwright 实例
        with sync_playwright() as p:
            print("Playwright is already installed.")
            # 检查 Chromium 浏览器是否安装
            browser_executable_path = p.chromium.executable_path
            print(browser_executable_path)
            if not os.path.exists(browser_executable_path):
                print("Chromium is not installed, downloading now...")
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                print("Chromium has been installed.")
    except ImportError:
        # 处理 Playwright 未安装的情况
        print("Playwright not installed, installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        # 再次尝试安装 Playwright 和浏览器
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

ensure_playwright_installed()