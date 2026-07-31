function EscCsv() { return '"' + ( -replace '"','""') + '"' }
Write-Host (EscCsv " hello world\)
