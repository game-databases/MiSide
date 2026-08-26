# Selects the site's art set from the extracted art export and emits
# web-sized WebP into public/img/. Run once per extraction rerun:
#   python scripts/select-art.py
#
# Selection table is CURATED (VC-1 fix #1): every row names the exported
# object it came from, so each image traces to client data. Mitas without a
# confident portrait get NO row — pages render their named empty well instead
# of a wrong image (design-standard §5.1 honesty without apology).
#
# Needs Pillow (present on this host); no new installs introduced.
import os
import sys
import json

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

ART = os.environ.get(
    "MISIDE_ART_EXPORT", "D:/unpacked_game_data/MiSide/art-export"
)
GGM = os.path.join(ART, "container-2d", "globalgamemanagers")
LEVEL2 = os.path.join(ART, "container-2d", "level2")
LOCALE_ART = os.path.join(ART, "localization-art")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "img")
# Generated manifest consumed by src/data/art.ts (client-dir-name keyed).
BOOKS_MANIFEST = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "books-art.json"
)

# character_id -> exported sprite (per-Mita menu portraits, sharedassets set;
# verified name-for-name against personages.resource_path).
MITA = {
    "mita-usual": "MitaIcon.png",  # the gallery icon slot's own art
    "mita-short-hairs": "Mita ShortHairs.png",
    "mita-kind": "Mita Kind.png",
    "mita-cap": "Mita Cap.png",
    "mita-little": "Mita Small.png",
    "mita-dreamer": "Mita Dreamer.png",
    "mila": "Mita Mila.png",
    "mita-creepy": "Mita Creepy.png",
    "mita-chibi": "Mita Chibi.png",
    "mita-black": "Mita Ghost.png",
    "mita-maneken": "Mita Maneken.png",
}

# Achievement icons: level2 menu atlas carries one square sprite per
# registry_index ([0]..[25], content-matched to achievements.jsonl rows),
# plus the game's own "no achievement" placeholder.
ACH = [
    "[0] Кислое молоко.png",
    "[1] Щелчок тьмы.png",
    "[2] Мертвый сок.png",
    "[3] Пингвинобеда.png",
    "[4] Сейф жизни.png",
    "[5] Победа мухи..png",
    "[6] О великая Мита!.png",
    "[7] Я нашел тебя!.png",
    "[8] Вкусная любовь..png",
    "[9] Условия выполнены.png",
    "[10] Разгоняйся!.png",
    "[11] Шлеп по голове!.png",
    "[12] Все игроки у меня..png",
    "[13] Привет Мита..png",
    "[14] Это конец.png",
    "[15] Разгоняйся до предела.png",
    "[16] Какое-то достижение.png",
    "[17] Великий танец..png",
    "[18] Длинный хвост.png",
    "[19] Ты не пройдешь!.png",
    "[20] Логи первой фазы.png",
    "[21 логи второй фазы..png",
    "[22] Адская победа.png",
    "[23] И без урона.png",
    "[24] Морковка..png",
    "[25] Задротище.png",
]
ACH_PLACEHOLDER = "Нет достижения.png"

UI = {
    "ui/cartridge": ("level2", "Cartridge.png"),
    "ui/tamagotchi": ("level2", "Interface Tamagotchi.png"),
    "ui/book": ("level2", "Book 1.png"),
    # Players section identity (VC-2 fix #3): the menu's own player-face icon,
    # verified name-for-name against the level2 UI object set.
    "ui/player": ("globalgamemanagers", "FacePlayer.png"),
    # Locations section identity (VC-2 fix #3): the apartment's own interior
    # door — the threshold every scene loads through, exported name-for-name
    # from the shared globalgamemanagers texture set.
    "ui/locations": ("globalgamemanagers", "Door Wooden 1.png"),
}

# Readable-book covers (books.jsonl ids): the in-game book texture IS the
# page surface, localized per client locale — so covers emit PER LOCALE under
# img/books/<client-dir-name>/ and pages serve their own locale's copy. A
# locale without the file on disk gets no manifest row (honest empty well).
BOOKS = {
    # book_id -> (texture dir, exported object)
    "books-0": ("Location House", "Books0.webp"),
    "books-1": ("Location House", "Books1.webp"),
    "books-2": ("Location House", "Books2.webp"),
    "books-4": ("Location House", "Books4.webp"),
    "book-1": ("Location19", "Book 1.webp"),
    "book-2": ("Location19", "Book 2.webp"),
    "book-3": ("Location19", "Book 3.webp"),
    "book-4": ("Location19", "Book 4.webp"),
}

# Per-minigame card art (VC-3 fix #3; served via MINIGAME_ART in src/data/art.ts).
# minigame_id -> (container, exported object). Every row is a CONFIDENT
# name-for-name match between the texture object and the minigame's own
# client identity, with the texture's non-shared container spread covering
# that game's pinned carrier/loader container (dataset-cartridges §4.2).
# menu-mita-dance and tamagotchi-find-furniture stay ABSENT: no named 2D
# object exists for them anywhere in the export (their surfaces are 3D-only)
# — those cards keep the honest empty well, never a substitute image.
MINIGAMES = {
    # loader level9 ("Minigame CarSpace"); Spacecar = the game's own screen
    "carspace": ("level9", "ScreenSpaceCar.png"),
    # loader level12 ("Minigame MakeManeken") — name-for-name
    "makemaneken": ("level12", "ScreenMakeManeken.png"),
    # dedicated scene level23: TextureGun spreads ONLY over level23+shared23
    "minigame-shooter": ("level23", "TextureGun.png"),
    # TelevisionGames rows are level6 carriers (DS-4 §5 offset pin)
    "fight": ("level6", "Background Fight.png"),
    "pinguin": ("level6", "Background Pinguins.png"),
    # Location4TableCardGame_Card classes + the Cards.png atlas both in level6
    "location-4-table-card-game": ("level6", "Cards.png"),
    # Location7_* carriers live in level9; the dance game's own pad object
    "location-7-game-dance": ("level9", "DanceButton.png"),
    # name-for-name with Location7_HammerButton (its answer icons)
    "location-7-hammer-button": ("level9", "ButtonHammer.png"),
    # PCSnaker carrier level16; Snaker spreads only over 16/17/21/22
    "location-14-pc-snaker": ("level16", "Snaker.png"),
    # PumpkinClicker carrier level19
    "location-17-pumpkin-clicker": ("level19", "Pumpkin.png"),
    # GamesCore_Main carriers are level15+level17 — both hold GameMachine
    "games-core": ("level15", "GameMachine.png"),
    # Tetris.png: the game's own block/board atlas (TetrisGame 1 is a sparse
    # 5%-opaque sprite that reads empty at card size)
    "tetris": ("level9", "Tetris.png"),
    # Tamagotchi activities: phone space is level3 (all four carriers)
    "tamagotchi-cooking": ("level3", "CookingTable.png"),
    "tamagotchi-help-trash": ("level3", "TrashBox.png"),
    "tamagotchi-sorting": ("level3", "RoomSorting.png"),
}


def emit(src, dest, max_side=512):
    im = Image.open(src)
    if max(im.size) > max_side:
        im.thumbnail((max_side, max_side), Image.LANCZOS)
    dest = os.path.join(OUT, dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    im.save(dest, "WEBP", quality=90, method=4)
    return os.path.getsize(dest)


def main():
    total = 0
    n = 0
    for cid, src_name in MITA.items():
        size = emit(os.path.join(GGM, src_name), f"mita/{cid}.webp")
        total += size
        n += 1
    for idx, src_name in enumerate(ACH):
        size = emit(os.path.join(LEVEL2, src_name), f"ach/{idx}.webp", max_side=256)
        total += size
        n += 1
    size = emit(os.path.join(LEVEL2, ACH_PLACEHOLDER), "ach/none.webp", max_side=256)
    total += size
    n += 1
    for dest, (base, src_name) in UI.items():
        size = emit(os.path.join(ART, "container-2d", base, src_name), f"{dest}.webp")
        total += size
        n += 1
    # per-minigame card art (VC-3 fix #3) — MINIGAME_ART in art.ts resolves these
    for mid, (container, src_name) in MINIGAMES.items():
        size = emit(
            os.path.join(ART, "container-2d", container, src_name),
            f"minigames/{mid}.webp",
        )
        total += size
        n += 1
    # per-locale book covers + the manifest art.ts resolves against
    books_manifest = {}
    for locale_dir in sorted(os.listdir(LOCALE_ART)):
        locale_path = os.path.join(LOCALE_ART, locale_dir)
        if not os.path.isdir(locale_path):
            continue
        have = []
        for book_id, (tex_dir, src_name) in BOOKS.items():
            src = None
            for root, _dirs, files in os.walk(locale_path):
                if os.path.basename(root) == tex_dir and src_name in files:
                    src = os.path.join(root, src_name)
                    break
            if src is None:
                continue
            size = emit(src, f"books/{locale_dir}/{book_id}.webp", max_side=512)
            total += size
            n += 1
            have.append(book_id)
        if have:
            books_manifest[locale_dir] = have
    with open(BOOKS_MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(books_manifest, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"select-art: {n} files, {total // 1024} KiB total under public/img/")


if __name__ == "__main__":
    main()
