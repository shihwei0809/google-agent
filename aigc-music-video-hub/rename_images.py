import os

workspace_dir = r"c:\GOOGLE ANGET\aigc-music-video-hub"
images_dir = os.path.join(workspace_dir, "圖片")

# Mapping from original cryptic name pattern to clean title-based name
rename_map = {
    "shiny_chemical_refinery_1781694488608.png": "01_夜幕精餾廠區.png",
    "molecular_design_ui_1781697630291.png": "02_化學分子模擬.png",
    "solvent_molecular_structure_holo_1781697302935.png": "03_全息分子模型.png",
    "automated_chemical_analysis_lab_1781696518552.png": "04_自動化實驗室分裝.png",
    "chemical_quality_control_1781697256156.png": "05_專業化學_QC_檢驗.png",
    "refinery_valves_close_1781697646257.png": "06_精餾閥門管道.png",
    "automated_bottling_line_1781697661097.png": "07_無塵自動化封裝線.png",
    "wafer_loading_cassette_1781697674541.png": "08_晶圓傳送天車.png",
    "wafer_chemical_cleaning_1781694502596.png": "09_晶圓溶劑清洗.png",
    "wafer_lithography_exposure_1781697273136.png": "10_曝光顯影製程.png",
    "wafer_patterning_close_1781697690809.png": "11_雷射光刻奈米雕刻.png",
    "automated_wafer_fab_cleanroom_1781696545154.png": "12_自動化黃光區無塵室.png",
    "glowing_cpu_semiconductor_hero_1781696434739.png": "13_高科技晶片核心.png",
    "green_solvent_recycling_concept_1781696530982.png": "14_廢溶劑綠色循環.png",
    "green_factory_wind_solar_1781697287532.png": "15_永續綠色科技廠房.png",
    "ai_supercomputer_server_1781696504007.png": "16_AI_超級電腦機房.png",
    "green_circular_economy_logistics_1781696421165.png": "17_環保港口與貨輪出海.png"
}

def main():
    print("開始重新命名圖片檔案...")
    for old_name, new_name in rename_map.items():
        old_path = os.path.join(images_dir, old_name)
        new_path = os.path.join(images_dir, new_name)
        
        # Perform rename
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
                print(f"重新命名: {old_name} -> {new_name}")
            except Exception as e:
                print(f"重新命名失敗 {old_name}: {e}")
        else:
            # Check if it was already renamed
            if os.path.exists(new_path):
                print(f"檔案已就緒: {new_name}")
            else:
                print(f"找不到檔案: {old_name}")
                
    print("\n圖片檔案重新命名完成！")

if __name__ == "__main__":
    main()
