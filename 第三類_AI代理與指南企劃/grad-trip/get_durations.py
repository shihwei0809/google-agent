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
    # Make each slide exactly 5.5 seconds long, letting the voice play and then fade to next slide naturally
    # (Since total video duration is 60 seconds, 11 slides * 5.5s is 60.5 seconds, which is absolutely perfect!)
    padded_dur = 5.5
    total += padded_dur
    print(f"  {{ i: {idx}, dur: {padded_dur}, raw: {round(dur, 1)} }},")
print("]")
print(f"Total Video Duration: {round(total, 1)} seconds ({round(total/60.0, 2)} minutes)")
