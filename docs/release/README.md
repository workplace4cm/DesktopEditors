# Secure Office Suite 1.0.0: release documentation

Secure Office Suite is an offline office suite for Windows and Ubuntu, built
from Euro-Office Desktop Editors. It installs as four separate applications:

| Application | Opens | Accent |
|---|---|---|
| EuroOffice Writer | DOC, DOCX, ODT, RTF, TXT | blue |
| EuroOffice Sheet | XLS, XLSX, ODS, CSV | green |
| EuroOffice Presentation | PPT, PPTX, ODP | orange |
| EuroOffice PDF | PDF, PDF forms | red |

| Document | For |
|---|---|
| [INSTALL.md](INSTALL.md) | Installing, upgrading, removing, and deploying without internet; a short user guide |
| [TECHNICAL.md](TECHNICAL.md) | How the suite is built, packaged, integrated with the OS and tested |
| [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md) | What this release does not do, open low-severity defects, and risks |
| [VALIDATION.md](VALIDATION.md) | The Phase 10 installation and release test plan and its results |

## What is in 1.0.0

- Four independent applications, each with its own launcher, icon, window, start page, recent documents, templates and file types.
- An Office-style ribbon in each editor (Home, Insert, Layout, Review, View and the application's own tabs), and a File menu (Backstage) with New, Open, Recent, Save, Save As, Print, Export, Protect, Info, Close and Options.
- A recent-documents list for each application that survives restarts, upgrades and reinstalls. You can pin, remove, clear and find missing files.
- 40 real local templates: Writer 13, Sheet 12, Presentation 10 and PDF forms 5. You can also add your own in *Documents/Secure Office Suite/My Templates*.
- Fully offline. There is no account, no cloud, no update check, no online help, no online templates, no plugins store and no URL scheme. Macros are disabled.
- Security hardening from the October 2026 review: links open without a shell, the native bridge is limited to the app's own pages, document parsing is hardened, and external workbook links are not fetched.
- Installation:
  - Windows installer with Start Menu entries and desktop shortcuts, file types and Default Apps registration, and clean uninstall.
  - Ubuntu .deb that installs with no internet on a standard Ubuntu 22.04 or 24.04 desktop.

The About box shows **Secure Office Suite, Version 1.0.0, © Secure Communications**. The packages carry the engine version 9.3.1. Ubuntu packages are numbered `9.3.1-sos.<build>` so that every newer build installs as an upgrade.

## Where the release packages come from

Every push to `main` runs **Build Secure Office Suite** (`.github/workflows/build.yml`). The run's artifacts are the release packages:

- `windows-packages-secure-office-suite-amd64`: the Windows installer (`.exe`) and a portable ZIP
- `linux-packages-secure-office-suite-amd64`: `secure-office-suite-desktopeditors_9.3.1-sos.<build>_amd64.deb`, the separate offline help package `-help`, and RPM/tar.xz builds (not tested, see the limitations)

A run is a release candidate only when all of its jobs are green. That includes `verify-templates`, `verify-apps`, `verify-windows` and `release-validation`. Pushing a tag such as `v9.3.1-1` publishes the same packages with a `SHA256SUMS` file as a GitHub Release. The release job runs only when every check passed.
