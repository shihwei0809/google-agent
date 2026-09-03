git checkout main
git merge feat/20260831 -m 'Merge feat/20260831'

$latestTag = git describe --tags --abbrev=0 2>$null
if (-not $latestTag) { $latestTag = 'v1.0.0' }
$parts = $latestTag.Trim('v').Split('.')
$parts[-1] = [int]$parts[-1] + 1
$newTag = 'v' + ($parts -join '.')

git tag $newTag
git push origin main --tags

Write-Output "Push successful, tag: $newTag"
