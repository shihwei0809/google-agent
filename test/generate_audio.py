import json
import os
import time
from gtts import gTTS

def generate_audios():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    story_path = os.path.join(script_dir, 'story.json')
    audio_dir = os.path.join(script_dir, 'assets', 'audio')
    
    # Ensure audio directory exists
    os.makedirs(audio_dir, exist_ok=True)
    
    # Load story.json
    with open(story_path, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
        
    print("Starting Traditional Chinese audio generation using gTTS...")
    count = 0
    
    # Iterate through pages, panels, and dialogues
    for page in story_data.get('pages', []):
        page_num = page.get('pageNumber')
        for panel in page.get('panels', []):
            panel_num = panel.get('panelNumber')
            for dialogue in panel.get('dialogues', []):
                d_id = dialogue.get('id')
                text = dialogue.get('text')
                speaker = dialogue.get('speaker')
                
                output_filename = f"{d_id}.mp3"
                output_path = os.path.join(audio_dir, output_filename)
                
                print(f"Generating audio for [{speaker}] on Page {page_num}, Panel {panel_num}: '{text}'")
                
                try:
                    # Create TTS object using Traditional Chinese (zh-TW)
                    tts = gTTS(text=text, lang='zh-TW', slow=False)
                    tts.save(output_path)
                    print(f"Saved: {output_filename}")
                    count += 1
                    # Small delay to respect rate limiting if running many requests
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error generating audio for {d_id}: {e}")
                    
    print(f"Finished. Total generated audio files: {count}")

if __name__ == '__main__':
    generate_audios()
