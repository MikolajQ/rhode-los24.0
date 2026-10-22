#!/usr/bin/env bash
# Kontrola tego, co trafi do obrazu: GApps przycięte przez patches/vendor_gapps/0001, Family Link (GmsSupervision).
# 17.10.2026: release 20261016 miał Velvet, talkback, Wellbeing, GoogleRestore, MarkupGoogle_v2 i GoogleFeedback,
# choć 0001 je wycina — wyszło dopiero na telefonie (to samo w a50s-los24.0, skąd ten skrypt).
#   check-image.sh pre  <korzeń>  przed kompilacją (krok „Szybki test kompilacji”, po m module-info): drzewo po łatkach
#                                 i lista pakietów produktu — błąd po minutach, nie po godzinach builda
#   check-image.sh post <korzeń>  po buildzie, przed podpisem: pliki w out/ — łapie też to, co weszło inną drogą
#                                 niż PRODUCT_PACKAGES (zależności, prebuilty), czego „pre” nie widzi
set -euo pipefail
MODE=${1:?pre|post}; ROOT=${2:?korzeń drzewa}
source "$(dirname "$0")/device.env"
OUT="$ROOT/out/target/product/$DEVICE"
PRUNED="Velvet talkback Wellbeing GoogleRestore MarkupGoogle_v2 GoogleFeedback SpeechServicesByGoogle PrebuiltExchange3Google"
REQUIRED="GmsSupervision"
bad=0; err() { echo "BŁĄD: $*"; bad=1; }
if [ "$MODE" = pre ]; then
  for f in arm64/arm64-vendor.mk common/common-vendor.mk; do
    for p in $PRUNED; do
      grep -qE "^[[:space:]]+$p( |\\\\|$)" "$ROOT/vendor/gapps/$f" && err "vendor/gapps/$f nadal dodaje $p (patches/vendor_gapps/0001 nie wszedł?)"
    done
  done
  PP="$OUT/product_packages.txt"
  if [ -s "$PP" ]; then
    for p in $PRUNED; do grep -qx "$p" "$PP" && err "$p na liście pakietów produktu ($PP)"; done
    for p in $REQUIRED; do grep -qx "$p" "$PP" || err "$p nie ma na liście pakietów produktu ($PP)"; done
  else
    echo "UWAGA: brak $PP — sprawdzone tylko drzewo"
  fi
elif [ "$MODE" = post ]; then
  for p in product/priv-app/Velvet product/app/talkback product/priv-app/Wellbeing product/priv-app/GoogleRestore \
           product/app/MarkupGoogle_v2 system_ext/priv-app/GoogleFeedback product/app/SpeechServicesByGoogle; do
    [ -e "$OUT/$p" ] && err "w obrazie jest $p (powinno być wycięte)"
  done
  [ -e "$OUT/product/priv-app/GmsSupervision/GmsSupervision.apk" ] || err "w obrazie brak product/priv-app/GmsSupervision (gapps-extras, Family Link)"
else
  echo "nieznany tryb: $MODE"; exit 2
fi
[ $bad -eq 0 ] && echo "check-image $MODE: OK"
exit $bad
