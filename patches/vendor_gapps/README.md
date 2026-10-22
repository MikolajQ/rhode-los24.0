# Patche na MindTheGapps (gałąź cinnamonbun)

Nakładane przez `scripts/apply-patches.sh` po `repo sync`, `git apply` na `vendor/gapps`.
Wygenerowane z drzewa `cinnamonbun` @bfa45ac (22.10.2026); po zmianach upstreamu: `git apply --check`,
w razie konfliktu wygenerować na nowo (`git diff` na sklonowanym MTG).

**Definicje modułów też usunięte (22.10.2026).** Samo wycięcie z `PRODUCT_PACKAGES` nie wystarczało: w obrazach
rhode 20261016 i a50s 20261015 były Velvet, VelvetTitan (w MTG tylko dla tangorpro!), talkback, MarkupGoogle_v2,
Wellbeing, GoogleRestore i GoogleFeedback — na A17 trafia do obrazu każdy `android_app_import` z przestrzeni nazw
`vendor/gapps/{arm64,common}`. Dlatego 0001 usuwa też ich bloki z `arm64/Android.bp` i `common/Android.bp`
(oraz SpeechServicesByGoogle, PrebuiltExchange3Google, dialer.support, libjni_latinimegoogle, wellbeing.xml).
Gdyby coś od nich zależało, wyjdzie to jako błąd soong w szybkim teście kompilacji; obraz sprawdza scripts/check-image.sh.

## 0001-prune-to-core.patch — zestaw jak NikGapps core + Android Auto

Wycięte (~385 MB): `Velvet` (242 MB), `SpeechServicesByGoogle` (66), `talkback` (34), `Wellbeing` + `wellbeing.xml` (22),
`GoogleRestore` (15), `MarkupGoogle_v2` (6),
`GoogleFeedback`, `PrebuiltExchange3Google`, `com.google.android.dialer.support(.xml)`, `libjni_latinimegoogle`.

Zostają: `GmsCore`, `Phonesky`, `GoogleServicesFramework`, `GooglePartnerSetup`, `AndroidAutoStub` (stub Android Auto —
NikGapps robi identycznie; pełną apkę doinstalowuje Play, pełna allowlist z NikGapps idzie przez gapps-extras), `SetupWizard` (na czas dodawania konta
dziecka; można wyciąć później), `GoogleCalendarSyncAdapter` + `GoogleContactsSyncAdapter` (3 MB, synchronizacja kontaktów
konta Google — WhatsApp z nich korzysta), wszystkie XML-e (permissions, sysconfig, default-permissions, hiddenapi),
`gapps.rc`, `gms_fsverity_cert.der`, overlaye `Gms*Overlay`.

`privapp-permissions-google-product.xml` zawiera blok `com.google.android.gms.supervision` — allowlist dla
GmsSupervision z gapps-extras; nie ruszać.
