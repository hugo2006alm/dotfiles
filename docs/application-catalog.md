# Application catalog contracts

`dependencies` lists other applications whose packages are required when an application is selected. `runtime_dependencies` describes runtime relationships and is not an instruction to install packages. Both fields reference catalog IDs. Installation resolution includes transitive installation dependencies; optional packages which do not correspond to a catalog application remain standalone package selections.

When declarations disagree on a package source, registry construction fails. A caller may provide an explicit `source_overrides` mapping for reviewed exceptions. This is separate from automatic official-repository detection during installation.

Reload strategies are `none`, `application`, `systemd-user-reload`, and `systemd-user-restart`. Systemd strategies require a valid user service; application strategies require a factory. Optional applications can list `runtime_executables`: when none are on PATH, their reload factory is not included. This check detects available executables only. It does not prove installation by package manager, active process, configured state, or working graphics.
