# Application registry

Add supported applications to `dotfiles_api/infrastructure/application_catalog.py`.
Each immutable `ApplicationSpec` owns packages and source overrides, application
dependencies, generator, output destinations, optional pure validator, refresh
factory/strategy, required flag, profiles and capabilities. This is a static Python
catalog, without runtime plugin discovery.

The CLI derives generators, output paths and refresh handlers from this catalog.
The desktop profile derives its base packages from the same declarations; detected
GPU and user-selected optional packages are still added by the profile resolver.
Optional application declarations can generate theme files without installing the
application (for example Vesktop).

Registry construction rejects duplicate IDs, missing dependencies, cycles, unsafe
relative paths and duplicate output destinations. Planning rejects undeclared,
missing or repeated generated artifacts and validates each artifact's syntax before
opening a transaction. Destinations remain restricted by EnvironmentContext.

To add a generator, implement its pure `render`, declare every returned artifact
ID and relative path, and select its refresh factory in one spec. Test both themes,
package routing, output validation and dry-run behavior. Do not add application
lists to the CLI or desktop profile.
