# Full build + 4K bake of the new set pieces, one after another; each bake's raw EXRs are deleted when it is done.
foreach ($p in 'boots', 'shins') {
    $d = "C:\Users\hossam.rabea\checkking-work\$p"
    & "$d\run_bake.ps1"
    Get-Content "$d\bake4k.log" -Tail 2
    Remove-Item "$d\tex\raw_*.exr" -Confirm:$false -ErrorAction SilentlyContinue
    "{0}: done, {1:N0} MB free" -f $p, ((Get-PSDrive C).Free/1MB)
}
