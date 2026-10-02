import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to insert a set to track generated batches
track_set_init = r'''
                    lorry_sources = list(getattr(self, "imported_lorry_files", []))
                    if not lorry_sources:
                        lorry_sources = glob.glob(os.path.join(self.base_dir, "Chemical_Lorry*.xlsx"))
                        if not lorry_sources:
                            error_msgs.append("⚠️ 找不到任何 Chemical_Lorry 檔案作為來源！")

                    lorry_generated_batches = set()
                    
                    for l_path in lorry_sources:
'''
content = content.replace(
    '                    lorry_sources = list(getattr(self, "imported_lorry_files", []))\n                    if not lorry_sources:\n                        lorry_sources = glob.glob(os.path.join(self.base_dir, "Chemical_Lorry*.xlsx"))\n\n                    for l_path in lorry_sources:',
    track_set_init
)

success_line = r'''
                                    success_lorry += 1
                                    lorry_generated_batches.add(b_no)
'''
content = content.replace('                                    success_lorry += 1', success_line)

# Add the check at the end of the lorry processing
end_check = r'''
                            except Exception as le:
                                error_msgs.append(f"產生 Chemical_Lorry 失敗: {le}")

                    # After checking all Lorry files, see which ones missed
                    for item in valid_data:
                        b_no = item["batch"]
                        if b_no not in lorry_generated_batches:
                            # if it failed because of factory, it's already in error_msgs, but it's fine to just add a general missing one if not in there
                            if not any(b_no in e for e in error_msgs):
                                error_msgs.append(f"⚠️ 批號 {b_no}：在來源 Lorry 檔案中找不到，無法產出該筆履歷。")
'''
content = content.replace(
    '                        except Exception as le:\n                            error_msgs.append(f"產生 Chemical_Lorry 失敗: {le}")',
    end_check
)

# And fix the summary message logic to always report even if 0
# The previous fix removed "and total_success_lorry > 0", but we should make sure it actually reports something
summary_logic = r'''
        if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get():
            msg_parts.append(f"• 單列 Chemical_Lorry：成功產生 {total_success_lorry} 份 (已自動對齊第 7 列)")

        dirs_str = "\n".join(all_output_dirs) if all_output_dirs else "(無產出資料夾)"
        msg = "\n".join(msg_parts) + f"\n\n檔案已儲存於資料夾：\n{dirs_str}"

        if total_error_msgs:
            msg += "\n\n部分錯誤 / 警告:\n" + "\n".join(set(total_error_msgs)) # deduplicate errors just in case
'''
content = content.replace(
    '        if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get():\n            msg_parts.append(f"• 單列 Chemical_Lorry：成功產生 {total_success_lorry} 份 (已自動對齊第 7 列)")\n\n        dirs_str = "\\n".join(all_output_dirs)\n        msg = "\\n".join(msg_parts) + f"\\n\\n檔案已儲存於資料夾：\\n{dirs_str}"\n\n        if total_error_msgs:\n            msg += "\\n\\n部分錯誤 / 警告:\\n" + "\\n".join(total_error_msgs)',
    summary_logic
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
