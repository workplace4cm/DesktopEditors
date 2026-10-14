#!/bin/bash
# Installs the packages listed in an Ubuntu desktop ISO manifest (the ones a
# container can hold), then the test tools, then removes the packages the old
# .deb asked for so they can't hide a missing dependency.
set -u
MANIFEST_URL=$1
TRIAL=${2:-0}
apt-get update -q
apt-get install -y -q curl ca-certificates > /dev/null
curl -fsSL "$MANIFEST_URL" | awk '{print $1}' | sed 's/:amd64$//' \
  | grep -Ev '^(linux-|grub|shim|casper|ubiquity|snapd|firefox|thunderbird|ubuntu-desktop|plymouth|cryptsetup|lvm2|mdadm|dmraid|os-prober|efibootmgr|secureboot|kpartx|zfs|initramfs|lupin|oem-|ubuntu-drivers|nvidia|cloud-init|open-vm-tools|spice|fwupd|bolt|thermald|wpasupplicant|systemd-oomd|gnome-initial-setup|snap|libsnapd|gir1.2-snapd|ubuntu-advantage|ubuntu-pro|apport|whoopsie|kerneloops|update-notifier|update-manager|unattended-upgrades|tracker|gnome-remote-desktop|ubuntu-release-upgrader)' \
  > /manifest.txt
# keep only names apt knows
apt-cache pkgnames | sort -u > /known.txt
sort -u /manifest.txt | comm -12 - /known.txt > /install.txt
echo "manifest packages: $(wc -l < /manifest.txt), installing: $(wc -l < /install.txt)"
xargs -a /install.txt apt-get install -y -q --no-install-recommends -o Dpkg::Options::=--force-confold > /apt-stock.log 2>&1 \
  || { echo "bulk install failed, retrying one by one"; tail -20 /apt-stock.log;
       while read -r p; do apt-get install -y -q --no-install-recommends "$p" >> /apt-stock.log 2>&1 || echo "skip $p"; done < /install.txt; }
dpkg --configure -a >> /apt-stock.log 2>&1 || true
# test tools
apt-get install -y -q --no-install-recommends xvfb openbox wmctrl xdotool imagemagick tesseract-ocr tesseract-ocr-eng python3 python3-pil sudo > /apt-tools.log 2>&1 || { tail -30 /apt-tools.log; exit 1; }
if [ "$TRIAL" != 1 ]; then
  for p in libxcb-cursor0 fonts-liberation fonts-liberation2 fonts-crosextra-carlito fonts-crosextra-caladea \
           fonts-dejavu fonts-dejavu-extra ttf-dejavu gstreamer1.0-libav gstreamer1.0-plugins-ugly \
           ttf-mscorefonts-installer fonts-takao-gothic fonts-takao; do
    dpkg -s "$p" > /dev/null 2>&1 && dpkg --purge --force-depends "$p"
  done
fi
dpkg-query -W -f '${Package}\t${Version}\t${Status}\n' > /installed-packages.txt
useradd -m -s /bin/bash tester
rm -rf /var/lib/apt/lists/*
exit 0
