param(
    [string]$Message = "Release 0.1.0",
    [string]$Branch = "main",
    [string]$Tag = "v0.1.0"
)

Write-Host "Staging all changes..."
git add -A

if ((git status --porcelain) -ne "") {
    git commit -m $Message
} else {
    Write-Host "No changes to commit"
}

Write-Host "Pushing branch $Branch to origin..."
git push origin $Branch

Write-Host "Creating tag $Tag and pushing..."
git tag $Tag
try {
    git push origin $Tag
} catch {
    Write-Host "Failed to push tag. Maybe it already exists. Error: $_"
}

Write-Host "Done."
