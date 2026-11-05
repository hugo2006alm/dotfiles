# Profiles and installation state

`dotfiles install --package spotify` selects only that package. Add `--profile desktop` to request desktop too. `dotfiles setup --interactive` explicitly enables the optional-package menu; setup does not prompt for optional packages by default.

Installation state version 2 stores profile choices in `requested_profiles` and personal selections in `explicit_packages`. `packages` is a snapshot for diagnostics, not permanent intent; resolve profile requirements against the current catalog. During migration from version 1, old `profiles` and `optional_packages` are retained, while historical resolved package lists are not promoted to explicit selections. Version 1 did not distinguish requested profiles from their dependencies, so its existing profile entries are conservatively retained.

`package_status` records installation; `desktop_configuration_status` separately records whether setup finished, failed or was interrupted. After preflight, setup records `in_progress` before installing; an interrupted or failed installation records `failed_or_partial` where possible. A sudden termination may leave `in_progress` for diagnosis and retry. `session_status` remains `not_checked` until a real session check exists. A completed package install is not evidence of a working graphical session.

The inventory reads package names from pacman local database metadata and fails closed if it is missing or malformed. It matches exact names only; virtual provides and version constraints are not evaluated. AUR checks distinguish empty results from network timeout, connection errors, HTTP errors and malformed replies; timeout and connection failures are retried once before failing preflight.
