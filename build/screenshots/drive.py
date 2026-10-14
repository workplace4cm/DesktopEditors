"""Drives an installed Secure Office Suite and screenshots the menus.

Finds UI text with Tesseract OCR and clicks it, so the same steps work on
Windows and Linux without hard-coded coordinates.

usage: drive.py OUT_DIR APP_COMMAND...
"""
import os
import subprocess
import sys
import time

WIN = sys.platform == "win32"
OUT = sys.argv[1]
APP = sys.argv[2:]
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "drive.log"), "a", encoding="utf-8")


def log(*a):
    print(*a)
    print(*a, file=LOG, flush=True)


if WIN:
    import ctypes
    from PIL import ImageGrab

    ctypes.windll.user32.SetProcessDPIAware()
    TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def shot(path):
        ImageGrab.grab().save(path)

    def click(x, y):
        u = ctypes.windll.user32
        u.SetCursorPos(int(x), int(y))
        u.mouse_event(2, 0, 0, 0, 0)
        u.mouse_event(4, 0, 0, 0, 0)

    def key(name):
        vk = {"Escape": 0x1B}[name]
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)

    def scroll(x, y, n):
        u = ctypes.windll.user32
        u.SetCursorPos(int(x), int(y))
        for _ in range(n):
            u.mouse_event(0x0800, 0, 0, -120, 0)
            time.sleep(0.1)

    def kill():
        subprocess.call(["taskkill", "/F", "/IM", "DesktopEditors.exe", "/T"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["taskkill", "/F", "/IM", "editors_helper.exe", "/T"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def maximize():
        pass
else:
    TESSERACT = "tesseract"

    def shot(path):
        subprocess.call(["import", "-window", "root", path])

    def click(x, y):
        subprocess.call(["xdotool", "mousemove", str(int(x)), str(int(y)), "click", "1"])

    def key(name):
        subprocess.call(["xdotool", "key", name])

    def scroll(x, y, n):
        subprocess.call(["xdotool", "mousemove", str(int(x)), str(int(y))])
        for _ in range(n):
            subprocess.call(["xdotool", "click", "5"])
            time.sleep(0.1)

    def kill():
        subprocess.call(["pkill", "-f", "/opt/secure-office-suite"])

    def maximize():
        subprocess.call(["wmctrl", "-r", ":ACTIVE:", "-b", "add,maximized_vert,maximized_horz"])


def ocr(path):
    """Returns [(text, x_center, y_center)] for the words on a screenshot."""
    from PIL import Image
    big = path + ".x2.png"
    im = Image.open(path)
    im.resize((im.width * 2, im.height * 2)).save(big)
    tsv = subprocess.run([TESSERACT, big, "stdout", "tsv"], capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stdout
    os.remove(big)
    words = []
    for line in tsv.splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        x, y, w, h = (int(v) / 2 for v in f[6:10])
        words.append((f[11].strip(), x + w / 2, y + h / 2))
    return words


def find(text, top=None, bottom=None, left=None):
    tmp = os.path.join(OUT, "_ocr.png")
    shot(tmp)
    words = ocr(tmp)
    os.remove(tmp)
    want = text.lower()
    hits = [w for w in words if w[0].lower().strip(".:") == want
            and (top is None or w[2] >= top) and (bottom is None or w[2] <= bottom)
            and (left is None or w[1] <= left)]
    log("find %r -> %s" % (text, [(int(x), int(y)) for _, x, y in hits]))
    return hits


def click_text(text, **kw):
    hits = find(text, **kw)
    if not hits:
        return False
    _, x, y = hits[0]
    click(x, y)
    return True


def snap(name, wait=3):
    time.sleep(wait)
    shot(os.path.join(OUT, name + ".png"))
    log("saved", name)


def start(args, wait=50):
    kill()
    time.sleep(3)
    log("start", APP + args)
    subprocess.Popen(APP + args, stdout=LOG, stderr=LOG)
    time.sleep(wait)
    maximize()
    time.sleep(5)


def dismiss_tips():
    for _ in range(3):
        if not click_text("Got"):
            break
        time.sleep(2)


def editor(tag, args):
    start(args)
    dismiss_tips()
    snap(tag + "-0-opened", 1)
    for tab in ("Insert", "View"):
        if click_text(tab, bottom=110):
            snap("%s-%s-tab" % (tag, tab.lower()))
    if click_text("File", bottom=110):
        snap(tag + "-file-menu")
        if click_text("Advanced"):
            snap(tag + "-advanced-settings")
            _, x, _ = find("Editing")[0] if find("Editing") else (0, 500, 0)
            for i in (1, 2):
                scroll(x, 400, 15)
                snap("%s-advanced-settings-%d" % (tag, i + 1))
            find("Macro")
            find("Macros")
        key("Escape")


def make_pdf(path):
    content = b"BT /F1 24 Tf 72 700 Td (Secure Office Suite test PDF) Tj ET"
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    open(path, "wb").write(out)


# start page and About
start([], wait=45)
snap("app-1-start-page", 1)
if click_text("About", top=400, left=300):
    snap("app-2-about")
    key("Escape")

editor("document", ["--new:word"])
editor("spreadsheet", ["--new:cell"])
editor("presentation", ["--new:slide"])
pdf = os.path.abspath(os.path.join(OUT, "..", "test.pdf"))
make_pdf(pdf)
editor("pdf", [pdf])
kill()
