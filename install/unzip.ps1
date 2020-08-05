param (
    [string]$source,
    [string]$destination
)

write ("Source : {0}" -f $source)
write ("Destination : {0}" -f $destination)

Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipFile]::ExtractToDirectory($source, $destination)

If(Test-path $destination) {
    write("Folder successfully written")
}