param([string]$TextPath, [string]$WavePath)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('Microsoft Hanhan')
$synth.Rate = 0
$synth.Volume = 100
$synth.SetOutputToWaveFile($WavePath)
$text = [System.IO.File]::ReadAllText($TextPath, [System.Text.Encoding]::UTF8)
$synth.Speak($text)
$synth.Dispose()
