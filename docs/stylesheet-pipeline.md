# Stylesheet compilation

Each `StylesheetSpec.source` is relative to the declarative `home/` tree. Sass imports may address sibling directories within that copied tree. Generated inputs default to their output basename beside the source; `input_paths` can map an input artifact ID to a relative subdirectory path. Absolute paths, parent traversal, duplicate destinations and source-file replacement are rejected.

Compilation runs against a private copy of `home/`. Source symlinks and special files are rejected. Source files are checked for modification during compilation and again just before commit. Generated inputs and final CSS are never written back to the checkout by the compiler. A separate process can still change a source after the last check; avoid editing templates while applying a theme.

`sassc` validates Sass syntax and produces CSS; it does not prove GTK accepts every property or that a service loaded the result. Verify light and dark themes inside an Arch/Hyprland session, inspect Waybar, Walker, SwayOSD and Wlogout, and check their user-unit logs after switching themes. Confirm a second application of the same theme produces identical CSS and no unnecessary refresh.
