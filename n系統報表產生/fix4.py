import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation
bad_indent = "                            except Exception as le:"
good_indent = "                        except Exception as le:"
content = content.replace(bad_indent, good_indent)

bad_indent2 = "                                error_msgs.append(f\"產生 Chemical_Lorry 失敗: {le}\")"
good_indent2 = "                            error_msgs.append(f\"產生 Chemical_Lorry 失敗: {le}\")"
content = content.replace(bad_indent2, good_indent2)

# Fix folder name
content = content.replace('三合一單輸出_', 'N系小包報表輸出_')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
