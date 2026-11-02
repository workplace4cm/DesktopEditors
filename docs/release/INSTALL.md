# Installing and using Secure Office Suite 1.0.0

Secure Office Suite needs no internet connection, either to install or to run. Copy the installer or package to the target PC on a USB drive or a network share and install it there.

- [System requirements](#system-requirements)
- [Check the files you copied](#check-the-files-you-copied)
- [Windows](#windows)
- [Ubuntu](#ubuntu)
- [Using the suite](#using-the-suite)
- [Where your data is kept](#where-your-data-is-kept)
- [Troubleshooting](#troubleshooting)

## System requirements

| | Windows | Ubuntu |
|---|---|---|
| Versions tested | Windows Server 2022 and 2025 (Windows 10/11 desktop family), 64-bit | Ubuntu Desktop 22.04 LTS and 24.04 LTS, 64-bit (amd64) |
| Disk | about 1.5 GB | about 1.5 GB |
| Memory | 4 GB or more recommended (each open application is its own process) | same |
| Rights | an administrator account to install | `sudo` to install |
| Network | none | none |

ARM computers, macOS and other Linux distributions are not supported in this release.

## Check the files you copied

The Windows installer is not code-signed yet (see [KNOWN-LIMITATIONS.md](KNOWN-LIMITATIONS.md)). Before you run it, compare its SHA-256 checksum with the one in `SHA256SUMS` from the release, or with the one you noted on the build machine.

- Windows (PowerShell): `Get-FileHash .\<installer>.exe -Algorithm SHA256`
- Ubuntu: `sha256sum secure-office-suite-desktopeditors_*.deb`

## Windows

### Install

1. Double-click the installer (`.exe`).
2. Windows SmartScreen may say *"Windows protected your PC"* because the installer isn't signed. Click **More info**, then **Run anyway**. Do this only if the checksum matched.
3. Follow the wizard. Keep **Associate file types** selected if Secure Office Suite should open Office, OpenDocument, text, CSV and PDF files.

The installer creates:

- four Start Menu entries: **EuroOffice Writer**, **EuroOffice Sheet**, **EuroOffice Presentation** and **EuroOffice PDF**;
- four desktop shortcuts with the same names, each with its own icon;
- the file types: DOC, DOCX, ODT, RTF and TXT go to Writer; XLS, XLSX, ODS and CSV to Sheet; PPT, PPTX and ODP to Presentation; PDF to PDF;
- all four applications in **Settings > Apps > Default apps**.

The program files go to `C:\Program Files\Secure Office Suite\DesktopEditors`.

### Install silently on many PCs

Run the installer from an administrator command prompt or a deployment tool:

```
<installer>.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /FULLASSOCIATION
```

| Option | Effect |
|---|---|
| `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART` | no windows, no questions, no restart |
| `/FULLASSOCIATION` | take all the file types listed above |
| `/NOASSOCPOLICY` | don't set Windows' *default associations* policy (use this when your domain already sets one) |
| `/DIR="D:\Apps\Secure Office Suite"` | install somewhere else |
| `/LOG="C:\Temp\sos-install.log"` | write a setup log |

Windows doesn't let a program set default applications for a user who is signed in. To get around that, the installer also sets the Windows *default associations* policy (`DefaultAssociations.xml` in the program folder). Every user gets the suite's file types at their next sign-in. The PDF type is the one exception: for the user who was signed in during the install, Windows keeps Microsoft Edge for PDF files until that user signs out and back in.

### Upgrade

Run the newer installer, by double-click or silently with the same options. You don't need to uninstall first. Settings, recent documents, your own templates, crash-recovery copies and your documents are all kept. The file types and shortcuts stay in place.

### Uninstall

Use **Settings > Apps > Installed apps > Secure Office Suite > Uninstall**. To uninstall silently, run `"C:\Program Files\Secure Office Suite\DesktopEditors\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART`.

- The uninstaller asks *"Do you want to clear the user settings and application cached data?"*. The default answer is **No**, and a silent uninstall always keeps them.
- Your documents and crash-recovery copies are never deleted.
- The file types go back to the applications that had them before. The shortcuts, Default Apps entries and the associations policy are removed.

### Reinstall

Run the installer again. Your settings and recent documents are picked up again unless you chose to clear them when you uninstalled.

## Ubuntu

### Install, without internet

The package lists only libraries that a standard Ubuntu Desktop 22.04 or 24.04 already has. The suite brings its own copies of everything else, including its fonts. Install it with `dpkg`, which never goes online:

```
sudo dpkg -i secure-office-suite-desktopeditors_9.3.1-sos.<build>_amd64.deb
```

If the PC has a local or online package source, `sudo apt install ./secure-office-suite-desktopeditors_*.deb` works too.

The offline help is a separate, optional package: `sudo dpkg -i secure-office-suite-desktopeditors-help_*.deb`. The **Help** tab in the editors shows the keyboard shortcuts in either case.

When `dpkg` reports missing dependencies, the PC isn't a standard Ubuntu Desktop install (a server or minimal install, for example). Copy the listed packages from a matching Ubuntu PC or ISO, or install them from your local mirror. `apt-get install --download-only` on a machine with the same release saves the `.deb` files in `/var/cache/apt/archives`.

The package installs:

- four applications in the app grid (**Show Apps**), in the Office category: EuroOffice Writer, Sheet, Presentation and PDF, each with its own icon. The suite entry itself is hidden.
- commands: `secure-office-suite-desktopeditors-writer`, `-sheet`, `-presentation` and `-pdf`, each taking file names;
- the default applications for DOC, DOCX, ODT, RTF, TXT, XLS, XLSX, ODS, CSV, PPT, PPTX, ODP and PDF, for every user (`/etc/xdg/mimeapps.list`). A user's own choice in **Settings** or in the file manager's **Open With** still wins.

To pin an application to the dock, open it, right-click its dock icon and choose **Pin to Dash**.

### Desktop shortcuts

Ubuntu keeps applications in the app grid and the dock, so the package doesn't put files on anyone's desktop. Each user who wants the shortcuts runs:

```
secure-office-suite-desktopeditors-desktop-shortcuts
```

To remove them again, run `secure-office-suite-desktopeditors-desktop-shortcuts --remove`.

### Upgrade

Install the newer package the same way (`sudo dpkg -i <newer>.deb`). Every build has a higher version number than the one before, so `dpkg` and `apt` treat it as an upgrade. Settings, recent documents, templates, recovery copies and documents are kept.

### Uninstall and reinstall

```
sudo apt remove secure-office-suite-desktopeditors     # or: sudo dpkg -r ...
sudo apt purge  secure-office-suite-desktopeditors     # also removes /etc settings
```

Neither command touches anything in users' home folders. The applications, menu entries, commands and default applications go away. Reinstalling with `dpkg -i` brings everything back with each user's settings and recent documents.

## Using the suite

### Starting an application

Start **EuroOffice Writer**, **Sheet**, **Presentation** or **PDF** from the Start Menu, the app grid, the desktop shortcut, or by double-clicking a document. Each application is independent:

- It has its own window, taskbar or dock icon, and start page.
- Double-clicking a document opens it in the application it belongs to, in the copy that is already running if there is one.
- Closing one application leaves the others running.

### Start page

Each application opens on its own start page:

- **New**: a blank document and the application's templates, with search and preview. *My templates* lists the files in `Documents/Secure Office Suite/My Templates`.
- **Recent**: that application's recent documents. You can pin a document, remove it from the list, clear the list, or locate a file that has moved. A missing file is marked; nothing on disk is ever deleted from here.
- **Open**: browse for a file. The file picker shows the application's own file types first.

### Editing

Each editor has an Office-style ribbon. It starts with **File**, **Home** and **Insert**, then has the application's own tabs (for example **Layout** in Writer, **Formulas** and **Data** in Sheet, **Slide Show** in Presentation, and **Page**, **Edit**, **Organize** and **Protect** in PDF), and ends with **Review**, **View** and **Help**. The **File** menu has:

- Home, New, Open and Recent;
- Save, Save As (every supported format) and Print;
- Export, which writes a copy: PDF, PDF/A, PNG or JPG; the PDF application also exports DOCX, ODT, RTF and TXT;
- Protect, Info and Open File Location;
- Close, Exit, Options and About.

Documents are saved in the format they came in unless you choose another one in **Save As**. The formats below are covered by the release tests; the engine opens more, and macro-enabled files open with their macros switched off.

| Application | Open and save |
|---|---|
| Writer | DOCX, DOC, ODT, RTF, TXT; templates DOTX; export to PDF |
| Sheet | XLSX, XLS, ODS, CSV; templates XLTX; export to PDF |
| Presentation | PPTX, PPT, ODP; templates POTX; export to PDF |
| PDF | PDF, PDF forms (view, annotate, edit text, fill and sign forms, organize pages) |

### Options and About

**File > Options** (or the start page's settings) holds the theme, language, units, autosave and recovery options. A change made in one application shows in the others after they restart. **File > About** shows the version (1.0.0) and the copyright holder (Secure Communications).

## Where your data is kept

| | Windows | Ubuntu |
|---|---|---|
| Settings | `HKEY_CURRENT_USER\Software\Secure Office Suite\DesktopEditors` | `~/.config/secure-office-suite/` |
| Recent documents (`sos-recents.json`), browser profiles, recovery copies | `%LOCALAPPDATA%\Secure Office Suite\DesktopEditors\data\` | `~/.local/share/secure-office-suite/desktopeditors/` |
| Your templates | `Documents\Secure Office Suite\My Templates` | `~/Documents/Secure Office Suite/My Templates` |

Back up these folders together with your documents. Upgrades and uninstalls keep them.

## Troubleshooting

| Problem | What to do |
|---|---|
| SmartScreen blocks the installer | Check the checksum, then **More info > Run anyway**. Signing the installer would remove this warning; see the limitations. |
| A PDF still opens in Edge after installing | Sign out and back in once. Or right-click a PDF, choose **Open with > Choose another app**, pick **EuroOffice PDF** and tick **Always**. |
| Windows asks at first start whether to make the suite the default | Answer once. Administrators can set `ignoreAssocMsg` = `true` (string) under the settings key above to skip the question. |
| `dpkg: dependency problems` on Ubuntu | The PC isn't a standard Ubuntu Desktop install. See [Install, without internet](#install-without-internet). |
| An application doesn't start on Ubuntu | Run its command from a terminal (`secure-office-suite-desktopeditors-writer`) and read the messages. A missing `libpulse0` or `libopengl0` means a minimal install. |
| A document opened in the wrong application | It can't. A document handed to another application is passed to the right one. If it persists, check the file's real type with `file <name>` (Ubuntu): a misnamed file opens by its content. |
| Fonts look different from Microsoft Office | Calibri, Cambria, Arial, Times New Roman and Courier New are replaced by metric-compatible fonts (Carlito, Caladea, Liberation), so line and page breaks stay the same. Install the Microsoft fonts on the PC if you have a licence for them. |
