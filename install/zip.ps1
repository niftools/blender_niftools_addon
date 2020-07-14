param (
    [string]$source,
    [string]$destination
)

write ("Source : {0}" -f $source)
write ("Destination : {0}" -f $destination)

If(Test-path $destination) {
write ("Ensuring existing archive is removed : {0}" -f $destination)
Remove-item $destination
write ("Existing archive removed successfully")
}

Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipfile]::CreateFromDirectory($source, $destination, 1, 1)
If(Test-path $destination) {
    write("File successully written")
}