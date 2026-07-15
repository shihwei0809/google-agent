# 將 AI 生成的圖片複製並重命名到 assets/images 目錄
import shutil, os

dir_path = os.path.dirname(__file__)
dest_dir = os.path.join(dir_path, "assets", "images")
os.makedirs(dest_dir, exist_ok=True)

brain_dir = r"C:\Users\C606\.gemini\antigravity\brain\e1f47725-b51a-44f4-9a30-977a29a4f90d"

MAPPING = {
    "grad_trip_dawn_1780055898764.png": "dawn.png",
    "grad_trip_bus_1780055917327.png": "bus.png",
    "grad_trip_highway_1780055934231.png": "highway.png",
    "grad_trip_park_1780055954323.png": "park.png",
    "grad_trip_ride_1780055970162.png": "ride.png",
    "grad_trip_camp_prep_1780055989464.png": "camp_prep.png",
    "grad_trip_party_1780056011891.png": "party.png",
    "grad_trip_sparks_1780056028416.png": "sparks.png",
    "grad_trip_hotel_1780056043718.png": "hotel.png",
    "grad_trip_packing_1780056063249.png": "packing.png",
    "grad_trip_beach_1780056078583.png": "beach.png"
}

for src_name, dest_name in MAPPING.items():
    src_path = os.path.join(brain_dir, src_name)
    dest_path = os.path.join(dest_dir, dest_name)
    print(f"Copying {src_name} -> {dest_name}...")
    shutil.copy(src_path, dest_path)

print("✓ 圖片複製與重命名完成！")
