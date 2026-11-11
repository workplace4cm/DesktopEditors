# Secure Office Suite 1.0.0

An offline office suite for Windows and Ubuntu: **SecureOffice Writer**, **Sheet**, **Presentation** and **PDF**, four independent applications with their own launchers, icons, start pages, recent documents, local templates and file types. Nothing in the suite connects to the internet.

## Downloads

| File | For |
|---|---|
| `Secure Office Suite-DesktopEditors-Standalone-9.3.1.0-x64.exe` | Windows 10/11 (64-bit) installer |
| `secure-office-suite-desktopeditors_9.3.1-sos.<build>_amd64.deb` | Ubuntu Desktop 22.04 / 24.04, installs with no internet (`sudo dpkg -i …`) |
| `secure-office-suite-desktopeditors-help_*.deb` | optional offline help for Ubuntu |
| `SHA256SUMS` | checksums: compare before installing |
| `SecureOfficeSuite-INSTALL.md` | installation, upgrade, removal and user guide |
| `SecureOfficeSuite-KNOWN-LIMITATIONS.md` | known limitations |
| `SecureOfficeSuite-VALIDATION.md`, `-TECHNICAL.md`, `-README.md` | test results, technical documentation, overview |

The portable ZIP, RPM and tar.xz files are included but were not part of the release testing.

## Before you install on Windows

The Windows installer in this release is **not code-signed**. Check its SHA-256 against `SHA256SUMS`. If Windows shows *"Windows protected your PC"*, choose **More info > Run anyway**; the User Account Control prompt shows "Unknown publisher". Copying the installer to the offline PCs on a FAT32/exFAT USB drive, or using **Properties > Unblock**, removes the download mark that makes SmartScreen check it.

## Tested

Clean install, launch, shortcuts, menus, file types, document opening, upgrade from the previous build, user-data preservation, uninstall, reinstall and offline use all passed on Ubuntu 22.04 and 24.04 and on Windows Server 2022 and 2025, with no network. No critical or high-severity issues are open. See `SecureOfficeSuite-VALIDATION.md`.
