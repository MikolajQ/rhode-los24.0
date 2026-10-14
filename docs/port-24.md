# Port na LineageOS 24.0 (Android 17) — rhode

Stan 14.10.2026. Przepis powstał z `rhode-los23.2` (0.2.0): ten sam układ i skrypty, baza
`lineage-24.0` (android-17.0.0_r1 + LineageOS), MindTheGapps `cinnamonbun`, yaap `sixteen` (bez gałęzi 17).

## rhode

- Jądro: fork `16.2-ksun` scala się z LineageOS `lineage-24.0` bez konfliktu (3 nowe commity LOS, `check-patches.sh`).
- Drzewa urządzenia: LineageOS `lineage-24.0` (device_motorola_rhode 10/10, sm6225-common 20/20, vendor 1/1 bez zmian).
- `hardware/qcom-caf/sm8250/media`: gałęzie 23.2 i 24.0 wskazują ten sam commit — łatka enkodera bez zmian.
- Grupa „opportunistic idle” SurfaceFlingera (0015–0019, 60 Hz po zakończeniu touch boostu) przeniesiona na nowy
  `RefreshRateSelector` (iteratory config group/global) — ważna dla baterii na panelu 90 Hz.

## Łatki: liczby

| projekt | 23.2 | 24.0 |
|---|---|---|
| `art` | 21 | 21 |
| `bionic` | 33 | 32 |
| `build_make` | 10 | 9 |
| `build_soong` | 23 | 22 |
| `device_motorola_rhode` | 10 | 10 |
| `device_motorola_sm6225-common` | 20 | 20 |
| `external_sqlite` | 3 | 3 |
| `frameworks_av` | 4 | 4 |
| `frameworks_base` | 225 | 220 |
| `frameworks_native` | 42 | 42 |
| `hardware_qcom-caf_sm8250_audio` | 1 | 1 |
| `hardware_qcom-caf_sm8250_media` | 1 | 1 |
| `packages_apps_Dialer` | 10 | 10 |
| `packages_apps_Launcher3` | 13 | 10 |
| `packages_apps_Settings` | 2 | 2 |
| `packages_modules_Bluetooth` | 1 | 1 |
| `packages_modules_CaptivePortalLogin` | 1 | 1 |
| `packages_modules_Connectivity` | 7 | 7 |
| `packages_modules_NetworkStack` | 2 | 2 |
| `packages_modules_Wifi` | 3 | 3 |
| `system_core` | 19 | 18 |
| `system_netd` | 3 | 3 |
| `tools_metalava` | 1 | 1 |
| `vendor_extra` | 1 | 1 |
| `vendor_gapps` | 1 | 1 |
| `vendor_lineage` | 15 | 15 |
| `vendor_motorola_sm6225-common` | 1 | 1 |

## Metoda portu

1. **Ocena** (`~/bin/los24/assess-patches.py`): każda łatka 23.2 na nową gałąź — `git apply`: 347/472.
2. **Port trójstronny** (`~/bin/los24/port-patches.sh`): per projekt repozytorium robocze z bazą 23.2 i 24.0, seria
   przez `git am -3`. Kluczowe: **bloby pośrednie** (`~/bin/los24/seed-blobs.sh`) — seria nakładana najpierw na
   starą bazę, żeby `git am -3` miał bazę scalania także dla łatek zmieniających plik zmieniony wcześniej w serii
   (bez tego 47 fałszywych konfliktów w frameworks_base zamiast 42 prawdziwych).
3. **Konflikty ręcznie**, w kolejności serii (`git am` → rozwiązanie → `--continue`), z kontrolą każdego API, którego
   dotyka łatka (symbole, sygnatury, flagi aconfig, zasoby). Gdzie upstream łatki ma już wersję na Androida 17,
   bierzemy ją: **CalyxOS `android17`** (stoi na LineageOS), **GrapheneOS `17`**, **crDroid `17.0`** (stoi na LineageOS).
4. **Eksport** (`~/bin/los24/export-series.sh`): `git format-patch --zero-commit` od czystego LOS 24.0, notki
   `[MikolajQ: …]` w opisach commitów (`~/bin/los24/port-note.py`).
5. **Kontrola**: `scripts/check-patches.sh` — wszystkie łatki wchodzą na aktualne lineage-24.0 (14.10.2026).

## Źródła wersji dla Androida 17

| łatka | skąd |
|---|---|
| Bluetooth timeout feature (`packages_modules_Bluetooth`) | CalyxOS `android17` 8a21c6fb88 (baza LineageOS — wchodzi bez zmian) |
| drop multicast when lockdown VPN enabled | GrapheneOS `17` 67a5069ac0, scalone z netd.c LOS 24.0 (bez drugiego `parse_skb()`) |
| prevent SO_BINDTODEVICE for uids under lockdown VPN | GrapheneOS `17` 4cf9ccdf76 |
| don't enable the "send DHCP hostname" option by default | GrapheneOS `17` 7ffb1ae38a |
| Launcher3: QuickstepTransitionManager: Fix and optimize transition animators | crDroid `17.0` 803e928a14 — zastępuje 0008 i 0011 z 23.2 |
| CachedAppOptimizer: don't crash system_server on kernels without memcg reclaim | jak crDroid `17.0` 359072b60100 |
| SystemUI: Caching tile viewmodels across qs fling | port ręczny, identyczny z crDroid `17.0` d009110a2482 |

### Łatki pominięte (z powodem)

| projekt | łatka 23.2 | powód |
|---|---|---|
| `bionic` | `0028-Performance-Optimization-for-memset-using-SIMD.patch` | Odrzucona: działa tylko na rdzeniach Qualcomm Oryon (__bionic_is_oryon) — SM6225 i Exynos 9611 ich nie mają; do tego błąd: if (HWCAP_ASIMD) sprawdza stałą, nie bit z _hwcap |
| `build_make` | `0010-core-Use-SOONG_ZIP-for-all-zip-usages.patch` | Odrzucona: zmienia tylko reguły pakietu emulatora i SDK (nie budujemy ich), a soong_zip i tak nie przyjmuje flag zip (-qjX/-rqX); w A17 reguła SDK się zmieniła |
| `build_soong` | `0019-soong-Disable-clang-tidy.patch` | Zbędna w A17: AOSP sam zrobił clang-tidy opcjonalnym (tylko moduły z tidy: true, a pliki .tidy powstają tylko przy WITH_TIDY/ALLOW_LOCAL_TIDY_TRUE) |
| `system_core` | `0017-init.rc-Disable-bootreceiver-traces-by-default.patch` | Już w A17: AOSP sam ustawia bootreceiver.enable 0 w on late-fs („to save 10MB of memory”) |
| `packages_apps_Launcher3` | `0008-Launcher3-Reduce-per-frame-allocations-in-QuickstepT.patch` | Zastąpiona przez crDroid 17.0 803e928a14 „QuickstepTransitionManager: Fix and optimize transition animators” (ten sam autor, port na A17) |
| `packages_apps_Launcher3` | `0011-Launcher3-Minimize-per-frame-allocations-and-calls-i.patch` | Zastąpiona przez crDroid 17.0 803e928a14 (ponowne użycie Rectów); cache wstawki paska nawigacji z 0011 porównywał dwie zawsze równe wartości (blokował odświeżanie) — crDroid go nie przeniósł |
| `packages_apps_Launcher3` | `0012-Launcher3-Minimize-per-frame-allocations-and-calls-i.patch` | Odrzucona: ponowne użycie jednej SurfaceTransaction przez wiele klatek ściga się ze scalaniem w RenderThread (crDroid 803e928a14 właśnie to naprawia w QuickstepTransitionManager), a współdzielony Rect z getTaskBounds() grozi aliasingiem w nowych wywołaniach A17; crDroid 17.0 jej nie niesie |
| `packages_apps_Launcher3` | `0013-Launcher3-Cache-spring-parameters-in-RectFSpringAnim.patch` | Odrzucona: w A17 parametry sprężyn przychodzą z obiektu config danej animacji (pola instancji, liczone raz w konstruktorze) — statyczny cache narzuciłby wszystkim animacjom wartości pierwszej |
| `frameworks_base` | `0106-Reduce-blocking-operation-on-display-thread.patch` | Już w A17: backport zmiany AOSP (Riddle Hsu, 08.2025) — rankTaskLayers w continueWindowLayout i invalidateTaskLayers z isLayoutDeferred są upstream, addToStopping zrefaktoryzowane |
| `frameworks_base` | `0121-SettingsState-downgrade-flags-spam-to-warning.patch` | Zbędna w A17: getAllAconfigFlagsFromSettings()/getFlagOverrideToSync() (i ten log) usunięte z SettingsState |
| `frameworks_base` | `0194-FrameTracker-Silence-logspam.patch` | Zbędna w A17: komunikatów „Missing HWUI/SF jank callback” już nie ma w FrameTracker |
| `frameworks_base` | `0208-Remove-extra-shade-expansion-trace-markers.patch` | Już w A17: commit AOSP (Caitlin Shkuratov, 10.2025) — git am pominął jako nałożony |
| `frameworks_base` | `0209-Remove-debug-logs.patch` | Już w A17: commit AOSP (Varun Murthy, 10.2025) — git am pominął jako nałożony |

### Łatki przeniesione ręcznie albo wzięte z innego projektu

Każda ma w opisie commita notkę `[MikolajQ: …]` — co zmienił Android 17 i jak to rozwiązano.

| projekt | łatka | notka |
|---|---|---|
| `tools_metalava` | lower maximum severity of UNFLAGGED_API lint to INFO | Ported to Android 17: the severity rule moved to FilteringReporter, UNEXPORTED_FLAGGED_API stays an error |
| `bionic` | make __stack_chk_guard read-only at runtime | Ported to Android 17: __libc_safe_arc4random_buf is now __libc_arc4random_buf_or_die |
| `bionic` | on 64-bit, zero the leading stack canary byte | Ported to Android 17: __libc_safe_arc4random_buf is now __libc_arc4random_buf_or_die |
| `bionic` | system_properties: Introduce native PropImitationHooks | Ported to Android 17: the hook runs before the new appcompat override lookup |
| `bionic` | Re-enable LTO for libm | Ported to Android 17: apex_available is now selected by release_deprecate_runtime_apex |
| `bionic` | libc: Set 100 instr-limit | Ported to Android 17: libc now takes afdo from libc_ndk_defaults, the property stays on libc itself |
| `art` | constify JNINativeMethod tables | Ported to Android 17: AtomicLong natives are gone, Unsafe lost compareAndSwap*, the trace_fib.cc test symlink stays a symlink |
| `art` | skip "speed"-optimized packages at an earlier dexopt stage | Ported to Android 17: the default package lists moved to ReasonMapping, so the filter now wraps both getDefaultPackagesForReason() calls in ArtManagerLocal; pre-reboot sync dexopt is skipped as well |
| `build_soong` | build: soong: use jemalloc by default and allow opt-in to scudo (2/4) | Ported to Android 17: kept the new Malloc_scudo_tsds_max and XOM variables |
| `system_core` | init.rc: Don't enable f2fs iostat by default | Ported to Android 17: AOSP moved iostat to an ro.debuggable=1 block, which userdebug builds still hit |
| `packages_modules_Bluetooth` | Bluetooth timeout feature | Android 17 version taken from CalyxOS android17 (8a21c6fb88), which is based on LineageOS |
| `packages_modules_Connectivity` | drop multicast when lockdown VPN enabled | Android 17 version from GrapheneOS 17 (67a5069ac0), merged into the LineageOS 24.0 netd.c: kept bpf_owner_firewall_match and reused the already parsed packet instead of a second parse_skb() |
| `packages_modules_Connectivity` | prevent SO_BINDTODEVICE for uids under lockdown VPN | Android 17 version from GrapheneOS 17 (4cf9ccdf76) |
| `packages_modules_Wifi` | don't enable the "send DHCP hostname" option by default | Android 17 version from GrapheneOS 17 (7ffb1ae38a) |
| `frameworks_native` | libbinder: Suppress log spam when unlinking death recipients | Ported to Android 17: kept the new message with the binder pointer |
| `frameworks_native` | Reduce thread scheduling overhead | Ported to Android 17: with fence_handling the background task also delivers buffer releases, so it is skipped only when there are no listener stats, buffer releases or fence mergers |
| `frameworks_native` | SF: Scheduler: opportunistically enter idle after touch | Ported to Android 17: the min/max mode iterators are now split into config group and global ones |
| `frameworks_native` | SF: Scheduler: set an expiration for heuristic layer's high refresh rate usages | Ported to Android 17: promotePacesetterDisplayLocked() was folded into promotePacesetterDisplay(), the heuristic idle timer starts there after the idle timer |
| `frameworks_native` | SF: Do not force idle refresh rate in some more scenarios | Ported to Android 17: the idle rate is computed before the new MRR full frame rate list |
| `frameworks_native` | SF: Bring back support for disabling backpressure propagation | Ported to Android 17: the pacesetter frame target is now a pointer |
| `frameworks_native` | surfaceflinger: vrr: apply idle signal to vrr rate policy | Ported to Android 17: promotePacesetterDisplayLocked() was folded into promotePacesetterDisplay() |
| `packages_apps_Launcher3` | Launcher3: Optimize AllApps perf and icon allocations | Ported to Android 17: IconCache is Kotlin now and BitmapInfo.withFlags() already skips NO_OP, the flags check moved to getBadgedIcon() |
| `packages_apps_Launcher3` | Launcher3: Add simple optimizations | Ported to Android 17: MultiValueUpdateListener is Kotlin now |
| `packages_apps_Launcher3` | Launcher3: QuickstepTransitionManager: Fix and optimize transition animators | Taken from crDroid 17.0 (803e928a14) in place of the Android 16 patches 0008 and 0011 (per-frame allocations in QuickstepTransitionManager) |
| `frameworks_base` | base: Add the ability to generate key pairs for keybox spoofing | Ported to Android 17: generateKey() now goes through retryBusyException() |
| `frameworks_base` | fwb: Disable some debug/log/trace | Ported to Android 17: the LightsService JNI is gone |
| `frameworks_base` | SystemUI: Fix imageloader spam in BrightnessSliderViewModel | Ported to Android 17: the view model is a HydratedActivatable now |
| `frameworks_base` | fwb: kill more debug spam | Ported to Android 17: ShellProtoLogGroup moved to Shell/protolog and lost the proto flag argument |
| `frameworks_base` | fwb: kill annoying appopservice log spam | Ported to Android 17: upstream now logs only blocked calls, with a stack trace; the log and the state read that only fed it are gone |
| `frameworks_base` | preventing media album bitmaps from impacting performance | Ported to Android 17: kept the new constructor layout |
| `frameworks_base` | center-cropping media bitmaps to improve quality | Ported to Android 17: the cropped bitmap is returned as a shared (ashmem) copy like upstream's createScaledAshmemBitmap(), and hardware or config-less bitmaps are handled |
| `frameworks_base` | Notification: Switch to low ram policy for bitmaps | Ported to Android 17: the low-RAM dimension variants and their code paths are gone, so the regular limits take the former low-RAM values (big picture 294x208dp, custom view image width 294dp) |
| `frameworks_base` | CUR_MAX_CACHED_PROCESSES is not greater than the maximum value allowed | Ported to Android 17: kept the new ProcessStateController updates |
| `frameworks_base` | CachedAppOptimizer: Fix persistent compact skipped | Ported to Android 17: PERCEPTIBLE_APP_ADJ is a static import now |
| `frameworks_base` | SystemUI: Caching tile viewmodels across qs fling | Ported to Android 17: TileViewModel takes the expandable as well, and TileGridViewModel is a HydratedActivatable |
| `frameworks_base` | core: Traversal last callback | Ported to Android 17: doCallbacks() no longer takes the frame interval |
| `frameworks_base` | core: Taversal last, skip relayout and hide by cache | Ported to Android 17: traversals are vsync callbacks now; the callback type is picked at post time and both queues are cleared on unschedule |
| `frameworks_base` | services: Reducing foldable sensor polling rate | Ported to Android 17: the hall sensor is gone from this provider |
| `frameworks_base` | core: Harden DeadSystem paths for optional services | Ported to Android 17: the dropbox tag check also takes the crash exception class, so the guarded helper got an overload for it |
| `frameworks_base` | services: Fix high-res wallpaper performance issue | Ported to Android 17: multiCrop is always on now; the upstream parenthesis slip in the minimum sample size is still fixed here |
| `frameworks_base` | services: Optimizing redundant status bar top hide checks | Ported to Android 17: the bar is reached through runWithStatusBarIfPresent(), whose result now gates the cached value |
| `frameworks_base` | run full explicit GC in SystemUI and system_server after locking | Ported to Android 17: KeyguardStateMonitor is gone, the system_server side now lives in the KeyguardServiceDelegate state callback |
| `frameworks_base` | core: Caching views to optimize performance | Ported to Android 17: doTraversal() takes the frame time and the barrier handling moved to removeTraversalBarrier() |
| `frameworks_base` | SystemUI: Change log level for multiple blur values emitted warning to debug | Ported to Android 17: the per-frame blur scheduling moved to BlurChoreographer |
| `frameworks_base` | libs: Reducing redundant surface animation processing | Ported to Android 17: the transformation and transaction moved to AnimationAdapter |
| `frameworks_base` | services Disable wm debug cpu hotspots | Ported to Android 17: AOSP fixed b/420917959 and moved the launch params log builder into LaunchParamsController, so the gate lives there now |
| `frameworks_base` | base: disable debug | Ported to Android 17: ClockRegistry no longer has DEBUG-gated logging, so it is left alone |
| `frameworks_base` | SystemUI: Gate WindowRootViewBinder logs behind DEBUG flag | Ported to Android 17: the blur plumbing moved to BlurChoreographer, the remaining binder logs are gated |
| `frameworks_base` | services: Silence some unneded logspam | Ported to Android 17: the start result is logged from logResult() now |
| `frameworks_base` | services: Fix appops spam | Ported to Android 17: the suppressErrorLogs argument is annotated now |
| `frameworks_base` | CachedAppOptimizer: don't crash system_server on kernels without memcg reclaim | Same as crDroid 17.0 (359072b60100) |
| `frameworks_base` | services: Optimizing wms prop \| settings reads | Ported to Android 17: the IME magnification observer is no longer flag-gated |


## Na co patrzeć przy pierwszym buildzie i starcie

- **Krok „Szybki test kompilacji”** kompiluje moduły zmieniane przez łatki — porty ręczne Java/Kotlin (WindowManager,
  SystemUI, ActivityManager, ART service) są sprawdzone na źródłach, ale nie były kompilowane lokalnie (pełne drzewo
  ~300 GB). Typowy błąd: zmieniona sygnatura w innym pliku niż łatka.
- **BPF/netd na starym jądrze**: Android 17 nie ma programów netd dla jąder < 5.10 (API 26Q2), a NetBpfLoad wymaga
  ≥ 5.10 od 25Q4 — tak samo jak 23.2. Działa dzięki podmianie wersji jądra na 5.10.239 (rhode: `ro.bpf.kver_override=5.10.239` w sm6225-common). BPF dalej
  kompilowany z `-mcpu=v1`, programy sockopt dla 5.10 te same co w 16. Po starcie: `pgrep netd`,
  `dumpsys connectivity | grep -A15 'Bpf Program Status'`, `logcat -b all | grep -i 'bpf\|netd'`.
- **yaap `sixteen`** (jemalloc_new, arm-optimized-routines) przy bionic z A17: moduły `libjemalloc5`,
  `libarm-optimized-routines-{string,mem,math}` istnieją, wszystkie 27 symboli AOR używanych przez ifunc-i bionic
  są zdefiniowane (sprawdzone 14.10). Kompilację potwierdzi dopiero build.
- **Funkcje z przełącznikiem** (z łatek 23.2, zostały): cache widoków `persist.sys.perf.view_cache` (domyślnie
  włączony — pompuje układy aktywności w tle; wyłącznik przy dziwnych błędach UI w aplikacjach),
  `persist.sys.activity_anim_perf_override` (domyślnie wyłączone), `window_ignore_secure` (Settings.Secure,
  domyślnie 0 — pozwala ignorować FLAG_SECURE także na buildzie niedebugowalnym; ustawia tylko adb/root).
- **Mniej logów**: brak linii `START u0 …` z ActivityStarter (tylko z `DEBUG_RESULTS`), wyciszone logi appops,
  WM Shell protolog, FrameTracker — przy debugowaniu startu aktywności pamiętać.
- **PIHooks**: `persist.sys.pihooks_*` w vendor/extra udają Pixela 10 Pro z Androidem 16 (BD3A.251105.010.E1) —
  na A17 bez zmian; przy utracie integralności świeży PIF jak dotąd.

## Wydania i aktualizacje

- `scripts/device.env`: `LOS_VERSION=24.0` — nazwa zipa (`sign.sh`, `upload.sh`), tytuł wydania, `"version"` w JSON-ie.
- **Osobny kanał Updatera `24.x/<urządzenie>.json`** (łatka `patches/vendor_extra`, `upload.sh`): telefon na 23.2
  czyta `23.x/…` i nie dostanie skoku 16 → 17 jako zwykłej aktualizacji. Przejście 23.2 → 24.0 ręcznie
  (sideload; GApps są w obrazie, ale skok wersji głównej najbezpieczniej z Format data).
- GApps: MindTheGapps `cinnamonbun` — GmsCore przychodzi jako APEX `com.google.android.gmssystem.prodvic`
  (`patches/vendor_gapps/README.md`); `scripts/inspect-zip.sh` sprawdza APEX zamiast `priv-app/GmsCore`.
