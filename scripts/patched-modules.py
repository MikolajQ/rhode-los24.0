#!/usr/bin/env python3
"""Moduły Soong/Make, które zmieniają łatki przepisu — dla kroku „Szybki test kompilacji” w ham.yml.

Po co: łatki nakładają się czysto (check-patches.sh), a potem nie kompilują się (brakujący symbol z łatki-pary
w innym projekcie, zmienione API w LineageOS). W pełnym buildzie taki błąd wychodził po 1-3 h; zbudowanie samych
dotkniętych modułów (z NINJA_ARGS="-k 0": wszystkie błędy naraz) zajmuje ułamek tego, a nic nie idzie na marne —
out/ zostaje dla pełnego builda.

Jak: dla każdego pliku zmienianego przez patches/<projekt>/*.patch szuka najdłuższego katalogu-przodka, który ma
moduły w $OUT/module-info.json (m module-info), i bierze stamtąd moduły instalowane na urządzenie (bez testów
i hosta). Wypisuje nazwy modułów, po jednej w linii; uwagi na stderr.

Użycie: patched-modules.py <korzeń drzewa> <katalog przepisu> <module-info.json> [limit na katalog]

Odporny na własne błędy: brak module-info.json albo wyjątek w skrypcie = ostrzeżenie na stderr i pusta lista
(krok testuje wtedy samo sepolicy). Test ma wcześniej wyłapać błędy łatek, a nie dokładać własnych awarii.
"""
import json, os, re, subprocess, sys
from collections import defaultdict


def main():
    root, recipe, info_path = sys.argv[1:4]
    per_dir = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    if not os.path.isfile(info_path):
        print(f"UWAGA: brak {info_path} — test kompilacji tylko sepolicy", file=sys.stderr)
        return
    run(root, recipe, info_path, per_dir)


def product_modules(root, info, info_path):
    """Moduły obrazu: product_packages.txt obok module-info (zostaje tylko po pełnym buildzie), a gdy go brak
    (świeży serwer, a50s 05.11: przez to test wziął sam Launcher3 i testy frameworku) — PRODUCT_PACKAGES z
    soong_ui --dumpvar-mode domknięte po required/shared_libs/system_shared_libs z module-info. None = bez filtra."""
    pp_path = os.path.join(os.path.dirname(info_path), "product_packages.txt")
    if os.path.isfile(pp_path):
        src, top = pp_path, open(pp_path).read().split()
    else:
        try:
            out = subprocess.run([os.path.join(root, "build/soong/soong_ui.bash"), "--dumpvar-mode", "PRODUCT_PACKAGES"],
                                 cwd=root, capture_output=True, text=True, timeout=1800, check=True).stdout
        except Exception as e:  # noqa: BLE001
            print(f"UWAGA: brak {pp_path} i dumpvar PRODUCT_PACKAGES zawiódł ({type(e).__name__}) — bez filtra obrazu",
                  file=sys.stderr)
            return None
        src, top = "dumpvar PRODUCT_PACKAGES", [w.split(":")[0] for w in out.split()]
    # domknięcie w obu przypadkach: sama lista produktu nie ma np. libc/init (APEX, inne nazwy instalacji)
    seen, stack = set(), list(top)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        m = info.get(n) or {}
        for k in ("required", "shared_libs", "system_shared_libs"):
            stack += [x.split(":")[0] for x in (m.get(k) or [])]
    print(f"lista produktu: {src} {len(top)} → domknięcie {len(seen)} modułów (required/shared_libs z module-info)",
          file=sys.stderr)
    return seen if len(top) > 50 else None   # podejrzanie krótka lista = lepiej bez filtra niż test bez modułów


def run(root, recipe, info_path, per_dir):
    SKIP_PROJECTS = ("kernel_",)             # jądro: lokalnie (~/bin/a50s/kernel-precheck.sh) i w pełnym buildzie
    TEST = re.compile(r"(^|[_.-])(tests?|Tests?|testing|benchmarks?|fuzzers?|robo|Robo)([_.-]|$)|Test(s)?$|Tests?[A-Z_]")

    with open(info_path) as f:
        info = json.load(f)

    # aplikacje i programy tylko te z obrazu: moduły spoza obrazu (np. sam Launcher3 obok Launcher3QuickStep,
    # checkinput ciągnący FrameworksCoreTests/FrameworksServicesTests) w LOS 17 potrafią się nie budować
    product = product_modules(root, info, info_path)

    by_dir = defaultdict(set)
    for name, m in info.items():
        if TEST.search(name) or name.endswith("-host") or "_host" in name:
            continue
        installed = m.get("installed") or []
        classes = m.get("class") or []
        on_device = any("/target/product/" in p for p in installed) or "JAVA_LIBRARIES" in classes
        if not on_device:
            continue
        # biblioteki natywne też tylko z obrazu: wariant .so modułu linkowanego statycznie (libcompositionengine
        # w LOS 24 ma UdfpsExtension.cpp podwójnie) nie buduje się, choć pełny build przechodzi (rhode 16.10)
        if product is not None and name not in product and "JAVA_LIBRARIES" not in classes:
            continue
        for d in m.get("path") or []:
            by_dir[d.rstrip("/")].add(name)


    def changed_files(patch):
        files = []
        with open(patch, errors="replace") as f:
            for line in f:
                if line.startswith("+++ b/"):
                    files.append(line[6:].strip())
                elif line.startswith("rename to "):
                    files.append(line[10:].strip())
        return files


    chosen, report = [], []
    patch_root = os.path.join(recipe, "patches")
    for proj_dir in sorted(os.listdir(patch_root)):
        if proj_dir.startswith(SKIP_PROJECTS):
            continue
        proj = proj_dir.replace("_", "/")
        if not os.path.isdir(os.path.join(root, proj)):
            print(f"[{proj_dir}] brak {proj} w drzewie, pomijam", file=sys.stderr)
            continue
        dirs = set()
        for p in sorted(os.listdir(os.path.join(patch_root, proj_dir))):
            if not p.endswith(".patch"):
                continue
            for rel in changed_files(os.path.join(patch_root, proj_dir, p)):
                if re.search(r"(^|/)(tests?|testing|robotests)/", rel):
                    continue
                d = os.path.dirname(os.path.join(proj, rel))
                while d and d not in by_dir and d != proj and "/" in d:
                    d = os.path.dirname(d)
                if d in by_dir:
                    dirs.add(d)
        mods = []
        for d in sorted(dirs):
            # najkrótsze nazwy pierwsze: zwykle główne moduły katalogu (framework, services, libc, Settings...)
            mods += sorted(by_dir[d], key=lambda n: (len(n), n))[:per_dir]
        mods = sorted(set(mods))
        report.append(f"[{proj_dir}] {len(mods)}: {' '.join(mods) if mods else '(brak modułów — sprawdzi pełny build)'}")
        chosen += mods

    for line in report:
        print(line, file=sys.stderr)
    for m in sorted(set(chosen)):
        print(m)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — każda awaria = test bez wyboru modułów, nie zatrzymanie builda
        print(f"UWAGA: patched-modules.py: {type(e).__name__}: {e} — test kompilacji tylko sepolicy", file=sys.stderr)
    sys.exit(0)
