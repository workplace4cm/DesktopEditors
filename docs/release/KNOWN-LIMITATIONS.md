# Secure Office Suite 1.0.0: known limitations

Severity uses the Phase 9 scale. There are no open critical or high-severity issues.

## Deployment

| # | Limitation | Impact | Workaround / plan |
|---|---|---|---|
| L1 | **The Windows installer is not code-signed.** | SmartScreen shows *"Windows protected your PC"*, and some antivirus or AppLocker policies may block unsigned installers. | Check the SHA-256 checksum, then **More info > Run anyway**, or allow the file by hash in your policy. Buying an OV/EV code-signing certificate and adding a signing step to `build-windows` removes the warning. This is an open decision. |
| L2 | **For the user who was signed in during the install, Windows keeps the previous choice for PDF (Microsoft Edge) and, on Windows 11 / Server 2025, asks once which application opens TXT files (Notepad had them)** until that user signs out and back in. | Double-clicking a PDF opens Edge, and a TXT shows "How do you want to open this file?" with EuroOffice Writer listed, in that session only. | The installer's default-associations policy applies at the next sign-in; or the user picks the EuroOffice application once with **Always**. Windows doesn't let installers change a signed-in user's choice, and the suite deliberately doesn't work around that protection. Other users and later sign-ins get the suite's file types. |
| L3 | **Windows client editions are tested through Windows Server 2022 and 2025** (the Windows 10 and 11 code base) on GitHub's runners, not on physical Windows 10/11 PCs. | Small differences are possible, such as Windows 11's own default-app prompts. | Do a pilot install on one target PC before a wide rollout. |
| L4 | **Only Ubuntu Desktop 22.04 and 24.04 on amd64 are supported and tested.** The RPM and tar.xz packages are built but not tested. There are no arm64 or macOS builds. | Other distributions may need extra libraries. | Use Ubuntu 22.04/24.04, or test on the other distribution first. |
| L5 | **Ubuntu server or minimal installs lack some libraries** (for example `libpulse0`, `libopengl0` and GTK). | `dpkg -i` reports dependency problems. | Copy those packages from a matching Ubuntu desktop or ISO. See INSTALL.md. |
| L6 | **No desktop shortcuts on Ubuntu by default.** | Users find the applications in the app grid and dock. | Each user runs `secure-office-suite-desktopeditors-desktop-shortcuts`. |
| L7 | **The engine and installer are versioned 9.3.1**, while the About box says 1.0.0. The Windows installer's file properties still include "Portions © Ascensio System SIA". | The two numbers can confuse support. | Use the Ubuntu package revision (`sos.<build>`) or the build run number to identify a build. |

## Product

| # | Limitation | Impact | Workaround / plan |
|---|---|---|---|
| L8 | **Offline only by design.** There is no co-editing, cloud storage, online templates, online help, plugins or update check. | Updates are installed by hand with a newer installer or package. | Distribute new builds through your software deployment tool. |
| L9 | **Macros don't run, and Content Controls are hidden.** | Macro-enabled documents open with macros switched off. | None needed; this is intentional. |
| L10 | **The Help tab has keyboard shortcuts only.** Full offline help is the optional `-help` package on Ubuntu, or part of the Windows installer. | — | — |
| L11 | **Microsoft fonts (Calibri, Cambria, Arial, Times New Roman…) aren't bundled.** Their licence forbids it. | Metric-compatible fonts are used instead (Carlito, Caladea, Liberation), so layout stays the same but glyphs look slightly different. | Install licensed Microsoft fonts on the PCs if exact glyphs matter. |
| L12 | **A theme or setting changed in one application reaches the others only after they restart.** | Each application has its own profile. | Restart the other applications. |
| L13 | **No "Combine PDFs" feature.** | Pages can be copied between documents inside EuroOffice PDF. | — |
| L14 | **Templates are checked by conversion and by opening in the editors.** Print fidelity of every template wasn't proofed on paper. | — | Report any template that prints badly. |

## Security

| # | Limitation | Impact | Plan |
|---|---|---|---|
| S1 | **The embedded browser engine (CEF/Chromium 109) is old** and runs without Chromium's sandbox. | Documents' scripts are restricted, but a browser-engine exploit would not be contained by a sandbox. Exposure is lower offline, with macros off and no online content. | A CEF upgrade is a separate project (planned since the October 2026 review). |
| S2 | **Some bundled image and XML libraries are old** (libxml2, libtiff, libpng, FreeType, xpdf derivatives). | Malformed files could exploit known bugs. Parsing was hardened, but the libraries weren't replaced. | Replace them together with the CEF upgrade. Open documents only from trusted sources until then. |
| S3 | **A release build honours `--remote-debugging-port`** (Phase 9 D2, low). | Someone who can already run programs as the user could inspect that user's open documents. That gives no extra privilege. | Kept because the automated regression suite drives the editors through it. It can be disabled in builds once the suite has another way in. |
| S4 | **Licence note.** The upstream licence contains an ONLYOFFICE clause about keeping its logo in the top-left corner (§7(b)), which this rebrand doesn't follow. | Legal, not technical. | Take legal advice before wide distribution outside the organisation. |

## Open low-severity and cosmetic defects (from Phase 9)

| ID | Defect | Severity |
|---|---|---|
| D1 | On Windows, a PDF made from a template sometimes shows in Recent as "opened" instead of "template" (seen in one run). | low |
| D4 | A file path that doesn't exist, given on the command line, opens a new blank document with no message (upstream behaviour). | low |
| D5 | The editor's internal page title is the placeholder "{{APP_TITLE_TEXT}} Documents". Window titles and taskbar names are correct. | cosmetic |
| D6 | On Ubuntu, a PDF made from a template is named in Recent with a coded string ("[32]I5SW…") instead of the template name. | cosmetic |

The Phase 9 medium finding D3 (EuroOffice Sheet could close after a CSV double-click on a fresh Windows install) has its result in [VALIDATION.md](VALIDATION.md).
