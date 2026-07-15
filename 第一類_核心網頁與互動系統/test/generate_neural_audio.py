import json
import os
import asyncio
import edge_tts

# Define mapping for characters to neural voices
VOICE_MAPPING = {
    "sakura": "zh-TW-HsiaoChenNeural", # 小妤 (11yo female) - Taiwanese female (child-like)
    "taiga": "zh-TW-YunJheNeural",      # 小融 (10yo male) - Taiwanese male voice, pitched up for boy
    "papa": "zh-TW-YunJheNeural",      # 爸爸 (宏志) - Standard Taiwanese male
    "mama": "zh-TW-HsiaoYuNeural"      # 媽媽 (美綠) - Standard Taiwanese female
}

# Rate modifiers to simulate ages and differentiate characters
RATE_MAPPING = {
    "sakura": "+0%",
    "taiga": "+15%", # Faster rate for the energetic 10yo boy
    "papa": "+0%",
    "mama": "+0%"
}

# Pitch modifiers to refine gender/age qualities (only pitch up Taiga to sound like a boy)
PITCH_MAPPING = {
    "sakura": "+0Hz",
    "taiga": "+35Hz", # Pitch shift YunJhe (male) up to sound like a boy
    "papa": "+0Hz",
    "mama": "+0Hz"
}

async def generate_single(text, voice, rate, pitch, output_path):
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)
        print(f"Generated: {os.path.basename(output_path)}")
    except Exception as e:
        print(f"Error generating {os.path.basename(output_path)}: {e}")

async def amain():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    story_path = os.path.join(script_dir, 'story.json')
    audio_dir = os.path.join(script_dir, 'assets', 'audio')
    
    os.makedirs(audio_dir, exist_ok=True)
    
    with open(story_path, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
        
    print("Generating high-quality neural voice MP3s using Microsoft Azure Neural TTS...")
    
    tasks = []
    for page in story_data.get('pages', []):
        for panel in page.get('panels', []):
            for d in panel.get('dialogues', []):
                d_id = d.get('id')
                text = d.get('text')
                speaker = d.get('speaker')
                
                voice = VOICE_MAPPING.get(speaker, "zh-TW-HsiaoChenNeural")
                rate = RATE_MAPPING.get(speaker, "+0%")
                pitch = PITCH_MAPPING.get(speaker, "+0Hz")
                output_path = os.path.join(audio_dir, f"ms_{d_id}.mp3")
                
                tasks.append(generate_single(text, voice, rate, pitch, output_path))
                
    await asyncio.gather(*tasks)
    print("Audio generation complete!")

if __name__ == '__main__':
    asyncio.run(amain())
