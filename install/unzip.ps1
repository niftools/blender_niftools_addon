param (
    [string]$source,
    [string]$destination
)

write ("Source : {0}" -f $source)
write ("Destination : {0}" -f $destination)

If(Test-path $destination) {
write ("Ensuring existing folder is removed {0}" -f $destination)
Remove-item $destination
write ("Success")
}

Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipFile]::ExtractToDirectory($source, $destination)

If(Test-path $destination) {
    write("Folder successfully written")
}