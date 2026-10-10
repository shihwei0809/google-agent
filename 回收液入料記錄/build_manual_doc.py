import os
def build():
    print("Generating manual docs (mock)...")
    with open("回收液入料記錄_操作手冊.docx", "w") as f:
        f.write("手冊內容")
    with open("回收液入料記錄_操作手冊.pdf", "w") as f:
        f.write("手冊內容")
    print("Done!")

if __name__ == "__main__":
    build()
