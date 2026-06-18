import os
import sys
import torch
import scipy.io.wavfile
from transformers import AutoProcessor, MusicgenForConditionalGeneration

# Ensure output encoding is UTF-8 for console messages
sys.stdout.reconfigure(encoding='utf-8')

def check_environment():
    print("===== 環境檢查 =====")
    print(f"Python 版本: {sys.version}")
    print(f"PyTorch 版本: {torch.__version__}")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA (NVIDIA 顯示卡加速) 是否可用: {cuda_available}")
    if cuda_available:
        print(f"顯示卡型號: {torch.cuda.get_device_name(0)}")
    else:
        print("警告: 未偵測到 CUDA。將使用 CPU 進行運算，生成速度會非常慢。")
    print("====================\n")
    return "cuda" if cuda_available else "cpu"

def generate_local_bgm(device, prompt, duration_seconds=15):
    print(f"正在載入 Meta MusicGen 模型 (facebook/musicgen-small)...")
    try:
        processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
        model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
        model.to(device)
    except Exception as e:
        print(f"模型載入失敗，請檢查網路連接或安裝依賴。錯誤: {e}")
        return

    print(f"開始本機音樂生成...")
    print(f"音樂提示詞: {prompt}")
    print(f"預計生成長度: {duration_seconds} 秒")
    
    # Calculate tokens based on duration (1 second is roughly 50 tokens for MusicGen)
    max_tokens = int(duration_seconds * 50)
    
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt",
    )
    
    try:
        # Generate audio tensor
        with torch.no_grad():
            audio_values = model.generate(
                **inputs.to(device),
                do_sample=True,
                guidance_scale=3,
                max_new_tokens=max_tokens
            )
            
        output_filename = "local_shiny_bgm.wav"
        # MusicGen outputs at 32000Hz sampling rate
        sampling_rate = 32000
        
        # Save WAV file
        scipy.io.wavfile.write(
            output_filename, 
            rate=sampling_rate, 
            data=audio_values[0, 0].cpu().numpy()
        )
        print(f"\n成功！本機生成音樂已儲存至：{os.path.abspath(output_filename)}")
        
    except Exception as e:
        print(f"音樂生成過程中發生錯誤: {e}")

if __name__ == "__main__":
    device = check_environment()
    
    # Prompt matching the style of Shiny Chemical MV
    prompt_text = "epic cyberpunk electronic rock with heavy industrial drums, distorted synthesizer, cinematic metal, 145 BPM"
    
    # Generate a 15-second demo track
    generate_local_bgm(device, prompt_text, duration_seconds=15)
