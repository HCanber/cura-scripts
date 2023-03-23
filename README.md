# Post Processing Scripts for Ultimaker Cura

This repo contains a collection of post processing scripts for [Ultimaker Cura](https://ultimaker.com/software/ultimaker-cura).

## Installation

1. In Cura, select _Help_ > _Show Configuration Folder_
1. Download a zip of this repository and extract it to the `scripts` folder, or clone this repository into the `scripts` folder
1. Restart Cura

The scripts should be available in the _Post Processing_ plugin, in Cura: _Extensions_ > _Post Processing_ > _Modify G-Code_.

## Scripts

### Insert g-code at layer

Inserts g-code at the specifed layers (use comma to separate multiple layers).
Use comma to separate multiple commands

### Stop After Layer

This script will stop the print after the specified layer, and will either remove the rest of the print or comment out the rest of the g-code.
Use `{machine_end_gcode}` as command to include the machine's normal end g-code (as configured in the machine settings in Cura).
Use comma to separate multiple commands.

Example:
To play a few beeps and then the normal end g-code

```
M300 S523 P100, M300 S660 P100, M300 S784 P100, M300 S523 P100, M300 S660 P100, M300 S784 P100, M300 S1046 P1000, {machine_end_gcode}
```

### Insert Mesh Print Size

Replaces all occurrences `%MINX%` `%MINY%` `%MINZ%` `%MAXX%` `%%MAXY%` `%%MAXZ%` with the actual size of the mesh in the GCODE
