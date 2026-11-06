# Secure Office Suite: technical documentation

This document is for the people who build, change and support Secure Office Suite. For installation, see [INSTALL.md](INSTALL.md).

## 1. Source layout

`workplace4cm/DesktopEditors` is the super-repository. It holds the build scripts, the CI and these documents, and pins every component as a git submodule:

| Submodule | Fork | What Secure Office Suite changes there |
|---|---|---|
| `desktop-apps` | workplace4cm/desktop-apps | the Qt shell (`win-linux/src`): the four applications, recent documents, template library, File-menu commands, About; the start pages (`common/loginpage`); templates (`common/templates/sos`); packaging (`package/`: Inno Setup, deb/rpm m4 templates, icons); test tools (`tools/sos-apps`, `tools/sos-templates`) |
| `web-apps` | workplace4cm/web-apps | the editors' UI: theme `secure-office-suite`, the Office-style ribbons (`SosRibbon.js`), the File menu (`SosBackstage.js`), hidden online, macro and Content Control features |
| `sdkjs`, `core`, `desktop-sdk` | workplace4cm forks | security hardening only: macro execution, plugin messaging, external links, document parsing, the native bridge's origin check |
| `dictionaries`, `document-templates`, `core-fonts`, `sdkjs-forms` | Euro-Office upstream | unchanged |

Pins on `main` are the source of truth. Each phase's PR in `DesktopEditors` bumps the submodule pins. The matching PRs in the submodule forks are record-only.

## 2. Build

`.github/workflows/build.yml` runs on every push to `main`, on tags and on pull requests:

| Job | Runner | Output |
|---|---|---|
| `version` | ubuntu | product version 9.3.1 (from `VERSION.txt`), build number, package build number `sos.<run number>` |
| `brand-assets` | ubuntu | icons and installer art rendered from the brand SVGs (overlay tarball) |
| `build-common` | ubuntu, Docker bake | editors web payload (sdkjs, web-apps, start pages, templates). It also runs the design-token, template-manifest and Qt unit tests (recent documents, application identities, template library) |
| `build-linux` | ubuntu, Docker bake | `.deb`, `-help.deb`, `.rpm`, `.tar.xz` → artifact `linux-packages-secure-office-suite-amd64` |
| `build-windows` | windows-2022, `build/windows/build.ps1` | Inno Setup installer and portable ZIP → artifact `windows-packages-secure-office-suite-amd64` |
| `verify-templates` | ubuntu, no network | every shipped template opened, saved and reopened with the package's own converter |
| `verify-apps` | ubuntu 24.04 + Xvfb | `verify_apps.sh` (40 checks on the four applications) and `verify_integration.sh` (menus, icons, default applications, double-click on 13 file types, desktop shortcuts, upgrade, remove, purge) |
| `verify-windows` | windows-2022 | `verify_windows.ps1`: silent install, Start Menu and desktop shortcuts, icons, Default Apps, 13 file types by double-click, upgrade, uninstall |
| `release-validation` | see §8 | offline clean install, upgrade from the previous main build, use, uninstall, reinstall, on stock Ubuntu 22.04/24.04 and Windows Server 2022/2025 |
| `publish-release` | ubuntu, tags only | GitHub Release with the packages, the release documents and `SHA256SUMS`. It needs every job above to be green |

A full build takes about two hours. The third-party libraries are built from source, with BuildKit and sccache caches. The submodule-only workflows `apps.yml`, `windows-install.yml`, `templates.yml` and `regression.yml` rerun their checks in minutes against the latest main build's packages. `release-validation.yml` can be run by hand on any two build runs.

### Versions

- The About box shows **1.0.0** (`desktop-apps/win-linux/src/version.h`, `ABOUT_VERSION_STR`).
- The engine and installer version is **9.3.1** (`VERSION.txt`).
- The Ubuntu package version is `9.3.1-sos.<build run number>`. The run number grows with every build, so each build installs as an upgrade over any earlier one, including the `9.3.1-dev.1` packages built before Phase 10. Only the packaging stage takes this number (`packages.args.BUILD_NUMBER`), so no compile cache is invalidated.

## 3. The four applications

There is one binary, `DesktopEditors(.exe)`. It runs as one of four applications chosen by `--app=writer|sheet|presentation|pdf`, or by the type of the document it is given. `desktop-apps/win-linux/src/cappidentity.{h,cpp}` is the single source for each application's id, name, extension table, single-instance mutex and port, Windows AppUserModelID, Linux desktop file name and WM_CLASS.

- **One process per application.** A second launch of the same application hands its documents to the running one. A document given to the wrong application, or to the suite command, is handed to the application that owns its type. The suite command itself only hands over and exits; there is no central launcher.
- **Separate state.** Each application has its own browser profile (`cache-<id>`) and recovery folder (`recover-<id>`). New profiles are seeded from the suite's settings. The recent list is shared on disk but filtered per application.
- **Start pages** (`common/loginpage/src/sos/`) are chosen by `?app=<id>`, with a per-application accent colour, New/Recent/Open panels, and the template gallery.

## 4. Recent documents

`win-linux/src/crecentdocuments.{h,cpp}` keeps `sos-recents.json` next to the engine's `recents.xml` in the user's data folder.

- One entry per normalised path, with application, origin (opened, new, template), timestamps, pin state, and size and mtime at the last check.
- Written atomically (QSaveFile + fsync), with a `.bak` per session. A damaged file is moved aside as `.corrupt`, and the backup or `recents.xml` is loaded instead.
- Fields this version doesn't know are kept on save, so older and newer builds can share the file.
- Remove and clear leave tombstones, so re-reading `recents.xml` doesn't bring entries back.
- The start page talks to it through `sos:recents:*` commands. Only paths on the list can be opened through them.
- The file survives upgrades and uninstalls. The release validation checks this (§8).

## 5. Templates

There are 40 templates in `desktop-apps/common/templates/sos/`: Writer 13 (`.dotx`), Sheet 12 (`.xltx`), Presentation 10 (`.potx`) and PDF forms 5. Each has a thumbnail and an entry in `manifest.js`. They are generated by `tools/sos-templates/make_templates.py` and installed under `<app>/converter/templates/sos`.

`win-linux/src/ctemplatelibrary.{h,cpp}` only creates documents from that folder or from *Documents/Secure Office Suite/My Templates*. `verify_templates.py` converts every template with the package's own `x2t`, with no network, in every build.

## 6. Editors: ribbon and File menu

- **Ribbons.** `web-apps/apps/common/main/lib/util/SosRibbon.js` holds the shared Review tab (Protection and Draw merged in) and the Help tab (keyboard shortcuts only). Each editor's `controller/Toolbar.js` calls `applyOfficeRibbon`. Presentation has a Slide Show tab, and PDF has Page, Edit, Organize and Protect. The Plugins tab is removed.
- **File menu.** `SosBackstage.js` builds the Backstage in each editor's `FileMenu.applyMode`. Shell commands are `sos:backstage:home|templates|about|exit`. Export writes copies; Save As offers every format.
- **Theme.** `web-apps/theme/secure-office-suite`. The design tokens (`tokens.less`) must be identical in the start page and the editors; `build-common` checks this with `cmp`.

## 7. Operating-system integration

### Windows (Inno Setup, `desktop-apps/package/inno`)

- Four `{autoprograms}` Start Menu entries and four `{autodesktop}` shortcuts, `DesktopEditors.exe --app=<id>`, with icons `icons\<id>.ico`.
- Per-application ProgIDs (`ASC.*`) with `--app=<id> "%1"` open commands. Each application has a Capabilities key under `RegisteredApplications`, so the four show in Default Apps.
- File types are taken over in HKLM. The previous ProgID is saved under `PreviousAssociations` and restored on uninstall.
- `DefaultAssociations.xml` plus the `DefaultAssociationsConfiguration` policy give every user the file types at their next sign-in. `/NOASSOCPOLICY` skips the policy. The installer deliberately doesn't forge UserChoice hashes or work around Windows' UCPD protection.
- Setup no longer runs the application during install or uninstall; that used to hang silent installs. Upgrades keep the user's language and settings (`createvalueifdoesntexist`).
- Uninstall asks before clearing settings (default **No**; silent = keep). It never deletes documents or `recover*` folders.

### Ubuntu (deb, `desktop-apps/package`)

- `/usr/share/applications/secure-office-suite-desktopeditors-<id>.desktop` (Office category, own icon in every hicolor size). The suite's own `.desktop` is `NoDisplay`.
- `/usr/bin/secure-office-suite-desktopeditors-<id>` wrappers.
- `postinst` merges the package's `mimeapps.list` into `/etc/xdg/mimeapps.list` between `# BEGIN/END … default applications` markers; `postrm` removes it. Purge doesn't touch home folders.
- `secure-office-suite-desktopeditors-desktop-shortcuts [--remove]` puts trusted launchers on the user's desktop.
- **Offline dependencies.** `Depends` lists only libraries that a stock Ubuntu Desktop 22.04/24.04 ships, such as `libpulse0`, `libopengl0` and GTK. `libxcb-cursor0`, Liberation, DejaVu, Carlito and Takao fonts are bundled in the application folder.

## 8. Release validation (Phase 10)

`.github/workflows/release-validation.yml` runs in every build and can be started by hand with `run-id` / `previous-run-id`:

| Platform | Machine | Sequence |
|---|---|---|
| Ubuntu 22.04, 24.04 | `desktop-apps/tools/sos-apps/stock-ubuntu`: a container with the package set of the official desktop ISO manifest plus test tools (Xvfb, xdotool), run with `--network none` | `verify_release_ubuntu.sh`: clean machine → `dpkg -i` the previous main build → open a document in each application → upgrade to this build (version must be newer; user files byte-identical; recents kept after restart) → purge (user data kept) → reinstall (menus, defaults and recents back). Then `verify_apps.sh` and `verify_integration.sh` on the same offline machine. |
| Windows Server 2022, 2025 | GitHub-hosted runner; installers and applications blocked by outbound firewall rules, with a watcher recording any connection they attempt | `verify_release_windows.ps1`: clean machine → silent install of the previous main build → use → upgrade (user files and registry settings kept) → uninstall (data kept) → reinstall → CSV double-click ×6 (3 on a brand-new profile) → no connection attempts. Then `verify_windows.ps1` (full integration) on a clean install. |

Results are in each job's summary and in the `release-*` artifacts (logs and screenshots). [VALIDATION.md](VALIDATION.md) maps the Phase 10 test list to these checks.

The functional regression suite from Phase 9 (`regression.yml`, `tools/sos-apps/regression`) drives the editors through the DevTools protocol with the network blocked. Run it by hand after product changes.

## 9. Security posture

These come from the October 2026 security review (`/mnt/project-files/rebrand/security/`):

- Online features are removed: cloud connections, sign-in, update checks, online templates and help, plugin store, URL scheme handler.
- External links open through the OS without a shell, and risky deep links are refused. The native bridge only answers the application's own pages. Macros are off (`customization.macros: false`), as are plugin messaging from documents and external workbook refresh.
- Document parsers are hardened in `core`, and CI actions are pinned by hash with minimal token scopes.

Open items are listed in [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md): the Chromium (CEF) upgrade, older image and XML libraries, and code signing.

### Installers (November 2026 review)

- **Windows**: setup and the uninstaller are built with DEP and ASLR. An install folder outside Program Files (`/DIR=` or the Folder page) gets the permissions of Program Files before any file is copied: owned by Administrators, SYSTEM and Administrators full control, Users read and run, nothing inherited, so a standard user cannot plant a DLL or swap a program that setup, the uninstaller or other users run. `vc_redist` is unpacked into setup's private temporary folder and must carry a valid Microsoft signature at build time. Setup makes nothing in `C:\ProgramData`, registers no URL protocol, service or scheduled task, and the uninstaller starts no program from the application folder.
- **Ubuntu**: the `.deb` has no dependency on `curl` or `wget`, no setuid or world-writable file, no URL handler, and its maintainer scripts only edit `/etc/xdg/mimeapps.list` between their own markers. *Open file location* no longer goes through a shell (a folder named like `$(command)` used to run it).
- **Build**: the Linux packaging image installs only Ubuntu's own packages (the NodeSource script piped into a shell and the unused npm package are gone).
- **Checks**: every build runs `desktop-apps/tools/sos-apps/audit_package_ubuntu.sh` (job `verify-apps`) and `audit_installer_windows.ps1` (job `verify-windows`, and the quick *Windows installer* workflow).

### Code signing

`build-windows` signs the build when a certificate is configured in the repository's **Settings > Secrets and variables > Actions**. The step *Prepare code signing* picks the method; `build/windows/build.ps1 -Sign -SignArgs …` then signs every `.exe` and `.dll` before packaging (`make.ps1 -Sign`) and the installer and uninstaller (`make_inno.ps1 -Sign`), and fails if the installer carries no signature. With no secrets the build is unsigned, as before. The job summary says which applies.

| Method | Secrets |
|---|---|
| Azure Trusted Signing (recommended) | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` (an app registration with the *Trusted Signing Certificate Profile Signer* role), `TRUSTED_SIGNING_ENDPOINT` (e.g. `https://weu.codesigning.azure.net`), `TRUSTED_SIGNING_ACCOUNT`, `TRUSTED_SIGNING_PROFILE` |
| A certificate file (`.pfx`), e.g. from your organisation's own CA | `WINDOWS_SIGNING_PFX` (the file, base64-encoded: `[Convert]::ToBase64String([IO.File]::ReadAllBytes('cert.pfx'))`) and `WINDOWS_SIGNING_PFX_PASSWORD` |

Public OV and EV certificates are now issued only on hardware tokens or cloud HSMs, so a `.pfx` is mainly for an internal CA, whose root must then be trusted on the target PCs (by Group Policy). Signatures are timestamped, so they stay valid after the certificate expires.

## 10. Making a release

1. Merge into `main` and wait for **Build Secure Office Suite** to be green, with every job passing.
2. Push a tag `v9.3.1-<n>` (for example `v9.3.1-1`). The tag build runs every check again, and `publish-release` creates a GitHub Release named after the first line of `docs/release/RELEASE-NOTES.md`, with those notes, the packages, the release documents and `SHA256SUMS`. The fork is public, so the release is public.
3. Copy the `.exe`, `.deb` (and `-help.deb`) and the checksums to the offline distribution medium.
