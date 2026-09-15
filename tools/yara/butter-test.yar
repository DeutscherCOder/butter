rule clutter_decoy_flag
{
    strings:
        $a = "CLUTTER{" ascii
    condition:
        $a
}
