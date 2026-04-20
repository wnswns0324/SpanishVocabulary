import tkinter as tk
from config import NOTION_TOKEN, DATABASE_ID
from modules.gui import SpanishAppGUI
from modules.llm_handler import LLMHandler
from modules.notion_client import NotionClient

def main():
    # 1. 인스턴스 생성 (의존성 주입 준비)
    llm_handler = LLMHandler()
    notion_client = NotionClient(NOTION_TOKEN, DATABASE_ID)

    # 2. GUI 생성 및 의존성 주입
    root = tk.Tk()
    app = SpanishAppGUI(root, llm_handler, notion_client)

    # 3. 앱 실행
    root.mainloop()

if __name__ == "__main__":
    main()