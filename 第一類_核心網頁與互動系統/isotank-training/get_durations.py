import os, subprocess, json

def get_duration(file_path):
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(res.stdout)
    return float(data["format"]["duration"])

dir_path = os.path.join(os.path.dirname(__file__), "assets", "narration")
files = sorted([f for f in os.listdir(dir_path) if f.endswith(".mp3")])

print("PAGES = [")
total = 0.0
for f in files:
    idx = int(f.split("-")[1].split(".")[0])
    dur = get_duration(os.path.join(dir_path, f))
    # Add a safety tail buffer of 3.0 seconds to let the user digest the slide animations as per specs (1.5s - 3s)
    padded_dur = round(dur + 3.0, 1)
    total += padded_dur
    print(f"  {{ i: {idx}, dur: {padded_dur}, raw: {round(dur, 1)} }},")
print("]")
print(f"Total Video Duration: {round(total, 1)} seconds ({round(total/60.0, 2)} minutes)")
