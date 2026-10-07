param(
    [Parameter(Mandatory=$true)][string]$ManifestPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -eq 'Microsoft Hanhan Desktop' } | Select-Object -First 1
if (-not $voice) { throw 'Missing installed Taiwanese Chinese voice: Microsoft Hanhan Desktop.' }
$synth.SelectVoice($voice.VoiceInfo.Name)
$synth.Rate = -1
$texts = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$chapter = [System.IO.Path]::GetFileNameWithoutExtension($ManifestPath).Substring(7, 2)
for ($i = 0; $i -lt $texts.Count; $i++) {
    $path = Join-Path $OutputDirectory ('chapter{0}_line{1:D2}.wav' -f $chapter, $i)
    $synth.SetOutputToWaveFile($path)
    $synth.Speak([string]$texts[$i])
    $synth.SetOutputToNull()
}
$synth.Dispose()
