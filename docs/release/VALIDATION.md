# Secure Office Suite 1.0.0: release validation

This document records how the Phase 10 installation tests were run and what they found. Every check is automated and runs again in every build (see [TECHNICAL.md §8](TECHNICAL.md#8-release-validation-phase-10)).

**Result: all 12 installation tests passed on Ubuntu 22.04, Ubuntu 24.04, Windows Server 2022 and Windows Server 2025, with no network. No critical or high-severity issue is open.**

## Build under test

| | |
|---|---|
| Build run | [41491130344](https://github.com/workplace4cm/DesktopEditors/actions/runs/41491130344) (PR #18, commit `7601462`), every job green |
| Ubuntu package | `secure-office-suite-desktopeditors_9.3.1-sos.64_amd64.deb` (artifact `linux-packages-secure-office-suite-amd64`) |
| Windows installer | `Secure Office Suite-DesktopEditors-Standalone-9.3.1.0-x64.exe` (artifact `windows-packages-secure-office-suite-amd64`) |
| Upgraded from | main build [41438930937](https://github.com/workplace4cm/DesktopEditors/actions/runs/41438930937) (commit `b9a3536`, package `9.3.1-dev.1`) |
| After the merge | main build [41556599099](https://github.com/workplace4cm/DesktopEditors/actions/runs/41556599099) (commit `7561048`): every job green again |
| Earlier runs of the same checks | release validation [41487849574](https://github.com/workplace4cm/DesktopEditors/actions/runs/41487849574) and [41491130977](https://github.com/workplace4cm/DesktopEditors/actions/runs/41491130977) (on the two latest main builds) |

### Machines

| Machine | How it was clean and offline |
|---|---|
| Ubuntu Desktop 22.04 and 24.04 | A container with exactly the package set of the official desktop ISO (current point release manifest), started with `--network none`, signed in as an ordinary user with sudo, under a virtual display. |
| Windows Server 2022 and 2025 | Fresh GitHub-hosted machines (the Windows 10 and 11 code base). Outbound firewall rules block the installers and the applications, and a watcher records every connection they attempt. |

### Totals for build 41491130344

| Job | Passed | Failed | Notes |
|---|---|---|---|
| Release validation, Ubuntu 22.04 | 183 | 0 | 0 |
| Release validation, Ubuntu 24.04 | 183 | 0 | 0 |
| Release validation, Windows Server 2022 | 196 | 0 | 2 (PDF, see below) |
| Release validation, Windows Server 2025 | 194 | 0 | 4 (PDF and TXT, see below) |
| verify-windows (Windows Server 2022) | 130 | 0 | 2 (PDF) |
| verify-apps (Ubuntu 24.04, applications and integration) | 127 | 0 | 0 |
| verify-templates (40 templates, no network) | all | 0 | — |

## The 12 installation tests

| # | Test | Ubuntu 22.04 / 24.04 | Windows 2022 / 2025 | What was checked |
|---|---|---|---|---|
| 1 | Clean installation on Ubuntu | pass | — | Nothing of the suite present first. `dpkg -i` with no network installs it; every library the applications load is present on a stock desktop. |
| 2 | Clean installation on Windows | — | pass | Nothing of the suite present first. Silent install with the network blocked; program folder, registry and uninstaller in place. |
| 3 | Independent launch | pass | pass | Each of the four applications starts from its own launcher on its own start page as its own process (four applications, four processes), with its own window class and icon. A second document goes to the application already running; the suite command only hands over and quits. |
| 4 | Desktop and Start Menu shortcuts | pass (desktop-shortcuts command) | pass | Windows: four Start Menu entries and four desktop shortcuts, each with its own icon, each starting the right application, after install, upgrade and reinstall. Ubuntu: the per-user desktop-shortcuts command creates and removes four trusted launchers. |
| 5 | Application menu | pass | pass | Ubuntu: four entries in the Office category, each starting its application, after install, upgrade and reinstall; the suite's own entry hidden. Windows: four applications in Default Apps. |
| 6 | File association | pass | pass (see note) | 13 file types (DOC, DOCX, ODT, RTF, TXT, XLS, XLSX, ODS, CSV, PPT, PPTX, ODP, PDF) belong to the right application; default applications are set once and removed on uninstall; previous owners restored on Windows. |
| 7 | Document opening | pass | pass | A sample of each type opened by double-click and by command line in the application that owns it; a document given to the wrong application is handed to the right one. |
| 8 | Upgrade | pass | pass | The previous main build was installed and used, then this build installed over it offline. The version is newer (`9.3.1-dev.1` → `9.3.1-sos.64`), menus, shortcuts and file types stay in place, all four applications start and open documents afterwards. |
| 9 | User-data preservation | pass | pass | Settings, recent documents, browser profiles, recovery folders and documents are byte-identical before and after the upgrade, after uninstall and after reinstall. The Windows language setting (fr-FR) survives. Each application's recent list still holds its document after the upgrade and a restart. |
| 10 | Uninstallation | pass | pass | Program files, menu entries, shortcuts, file types and default applications removed. Users' data and documents kept (Ubuntu purge; Windows silent uninstall). |
| 11 | Reinstallation | pass | pass | Reinstalled offline; menus, shortcuts and file types back; settings and recent documents picked up again; double-click on an ODT opens Writer. |
| 12 | Offline installation and operation | pass | pass | Ubuntu machines have no network at all. On Windows the watcher saw no connection attempt by the installers or the applications. All 40 templates open offline (verify-templates). |

## Phase 9 finding D3 (medium): closed, not reproduced

*"EuroOffice Sheet may close after a CSV double-click on a fresh Windows install."* The release validation double-clicks a CSV six times on each Windows machine, three of them on a brand-new profile (settings and data wiped first), and checks that Sheet is still running 15 seconds later.

| Run | Windows 2022 | Windows 2025 |
|---|---|---|
| Build 41491130344 | 6 of 6 kept Sheet open | 6 of 6 kept Sheet open |
| Release validation 41491130977 | 6 of 6 | 6 of 6 |
| Release validation 41487849574 | 6 of 6 | 6 of 6 |

The double-click check in verify-windows (main build 41438930937 and this build) also passed. D3 is closed as not reproduced. The check stays in every build, so a regression would turn the build red.

## Notes (not failures)

- **PDF on Windows, and TXT on Windows Server 2025 / Windows 11, for the user signed in during the install.** Windows keeps Edge for PDF and asks once which application opens TXT files, because it doesn't let installers change a signed-in user's choice. The installer's default-associations policy gives both to the suite at the next sign-in; other users get them straight away. Documented as L2 in [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md). The checks confirm the ProgID and its open command are correct and open the file in the right application.

## Not verified here

- Physical Windows 10 and Windows 11 PCs (Server 2022/2025 share their code base). A pilot install on one target PC is recommended (L3).
- The effect of the default-associations policy at an actual next sign-in. CI machines can't sign out and back in; the policy file and registry key were checked.
- The RPM and tar.xz packages, other distributions and ARM (L4).
- The installer's interactive wizard pages. All installs ran silently with the same options the wizard sets.
