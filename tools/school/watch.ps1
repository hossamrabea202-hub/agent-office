# Waits for the owner's next order in the School room thread, prints it and exits.
# Uses no AI tokens while it waits. Run it in the background; restart it after handling an order.
# GitHub's 304 replies don't count against the 60 requests/hour limit, so a 60 s poll is safe.
param([int]$Every = 60, [string]$State = "$env:TEMP\school-chat-seen.txt", [string]$Api = "https://api.github.com/repos/hossamrabea202-hub/agent-office")
$owner = 'hossamrabea202-hub'
$api = $Api
$title = 'School room: orders for School Assistant'
$tags = @{}
function Get-Json([string]$url) {
  $h = @{ Accept = 'application/vnd.github+json' }
  if ($tags[$url]) { $h['If-None-Match'] = $tags[$url].tag }
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -Headers $h
    $data = [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json
    $tags[$url] = @{ tag = $r.Headers['ETag']; data = $data }
    return , $data
  } catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 304) { return , $tags[$url].data }
    return , $null
  }
}
$seen = 0
if (Test-Path $State) { $seen = [long](Get-Content $State -TotalCount 1) }
$issue = 0
while ($true) {
  if (-not $issue) {
    $list = Get-Json "$api/issues?creator=$owner&state=open&sort=created&direction=desc&per_page=50"
    if ($list) { $hit = @($list | Where-Object { $_.title -eq $title }) | Select-Object -First 1; if ($hit) { $issue = $hit.number } }
  }
  if ($issue) {
    $list = Get-Json "$api/issues/$issue/comments?per_page=100"
    # Anyone on GitHub can comment on a public issue, so only the owner's account counts.
    $new = @($list | Where-Object { $_.user.login -ceq $owner -and $_.id -gt $seen })
    if ($new.Count) {
      foreach ($c in $new) { "ORDER $($c.id) $($c.created_at)"; $c.body; '---' }
      ($new | Measure-Object id -Maximum).Maximum | Out-File $State -Encoding ascii
      exit 0
    }
  }
  Start-Sleep $Every
}
