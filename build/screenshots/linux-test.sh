#!/bin/bash
# Runs inside the stock-desktop container with no network.
set -x
OUT=/out
DEB=$(ls /pkg/*.deb | grep -v -- -help | head -1)
cp /installed-packages.txt /apt-stock.log $OUT/ 2>/dev/null
lsb_release -ds > $OUT/os.txt 2>/dev/null || cat /etc/os-release > $OUT/os.txt
dpkg-deb -I "$DEB" > $OUT/deb-info.txt
for p in libxcb-cursor0 fonts-liberation fonts-crosextra-carlito ttf-mscorefonts-installer fonts-takao-gothic gstreamer1.0-libav; do
  printf '%-28s %s\n' "$p" "$(dpkg-query -W -f '${Status}' $p 2>/dev/null || echo 'not installed')"
done > $OUT/before-install.txt
( curl -sS -m 5 https://archive.ubuntu.com >/dev/null 2>&1 && echo "network: reachable" || echo "network: none" ) >> $OUT/before-install.txt
dpkg -i "$DEB" > $OUT/dpkg-install.log 2>&1
RC=$?
echo "dpkg -i exit code: $RC" >> $OUT/dpkg-install.log
PKG=$(dpkg-deb -f "$DEB" Package)
dpkg -s "$PKG" | head -3 >> $OUT/dpkg-install.log
if [ $RC != 0 ]; then
  echo "INSTALL FAILED" > $OUT/RESULT
  [ "${TRIAL:-0}" = 1 ] || exit 1
  dpkg -i --force-depends "$DEB" >> $OUT/dpkg-install.log 2>&1
fi
cd /opt/secure-office-suite/desktopeditors
for f in DesktopEditors platforms/libqxcb.so; do echo "== $f"; LD_LIBRARY_PATH=$PWD:$PWD/converter ldd "$f" | grep "not found"; done > $OUT/missing-libs.txt 2>&1
ls fonts > $OUT/app-fonts.txt 2>&1
chown -R tester $OUT
sudo -u tester -H bash -c '
  export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
  Xvfb :99 -screen 0 1600x1000x24 & sleep 3
  openbox & sleep 2
  cd /out && python3 /tools/drive.py /out/shots /usr/bin/secure-office-suite-desktopeditors
' > $OUT/drive-console.log 2>&1
[ -f $OUT/RESULT ] || echo "INSTALL OK" > $OUT/RESULT
