try {
    Copy-Item -Path "C:\ProgramData\Google\Chrome Remote Desktop\host.json" -Destination "C:\Users\C606-PC\.gemini\antigravity\brain\bf1ea0cd-6e63-4ca8-8565-03c4beddaf51\scratch\host_info.json" -Force
    "SUCCESS" | Out-File "C:\Users\C606-PC\.gemini\antigravity\brain\bf1ea0cd-6e63-4ca8-8565-03c4beddaf51\scratch\copy_status.txt"
} catch {
    $_.Exception.Message | Out-File "C:\Users\C606-PC\.gemini\antigravity\brain\bf1ea0cd-6e63-4ca8-8565-03c4beddaf51\scratch\copy_status.txt"
}
