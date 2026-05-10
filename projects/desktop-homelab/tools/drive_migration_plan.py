"""drive_migration_plan.py — Phase A action list.

Edit this file to control what drive_migration_stage.py does.
Re-run drive_migration_stage.py (no flags) for a dry-run preview.
Run with --execute when satisfied.

Action kinds:
    "copy"   — copy source → dest (recursive). Original is NEVER touched.
    "skip"   — explicitly do nothing; document why so the audit trail is clear.
    "review" — flag for human inspection; size is reported but no copy.

Source paths are Windows raw strings (use r"...").
Dest paths land under E:\\_migration\\ (the DEST_ROOT below).
Originals on C: and F: are read-only throughout Phase A; deletion happens
manually after Linux install confirms data integrity.

Inputs:  edit PLAN below
Outputs: consumed by drive_migration_stage.py

Decision history:
    2026-05-09 v1 — initial plan with reviews pending
    2026-05-10 v2 — Chip's review applied:
        - Downloads can be deleted (skip)
        - .vscode extensions excluded
        - Cadence + EAGLE: copy whole tree (guitar pedal design files mixed in;
          sort post-Linux)
        - Peshka, SPB_Data, wdl-ol, wf: skip
        - .Neo4jDesktop, C:\\bin, C:\\Devices: skip
        - chipj_000 + F:\\MuseScore: removed (don't exist)
        - HTTPS-only confirmed for D:/_code repos; .ssh/.gnupg explicitly skipped
        - Added separate staging actions for F:\\Users\\Chip\\Pictures and the
          iTunes Voice Memos folder so Phase B can pick them up without
          digging into the F-Chip backup tree.

Phase B notes (for the post-Linux script):
    - F-Chip\\Pictures → consolidate with master picture collection on E: NAS
    - F-voice-memos → /srv/media/voice-memos/ (production side)
    - F-Chip\\Music (other) → /srv/media/music/ (consumption side)
"""
from dataclasses import dataclass, field


@dataclass
class Action:
    kind: str
    source: str
    description: str
    dest: str = ""
    excludes: list[str] = field(default_factory=list)


DEST_ROOT = r"E:\_migration"

# Common AppData exclusion list — caches and crash reports we don't want to ship.
APPDATA_CACHE_EXCLUDES = [
    "Cache", "Cache_Data", "Code Cache", "GPUCache", "ShaderCache",
    "Service Worker", "blob_storage", "IndexedDB", "Local Storage",
    "Crashpad", "Crash Reports", "logs", "*.log", "*.tmp",
]


PLAN = [
    # ============================================================
    # C:\Users\chipj — active Windows user profile
    # ============================================================

    # --- Personal documents and media ---
    Action("copy", r"C:\Users\chipj\Documents",
           "Documents folder",
           dest=rf"{DEST_ROOT}\C-chipj\Documents"),
    Action("copy", r"C:\Users\chipj\Desktop",
           "Desktop",
           dest=rf"{DEST_ROOT}\C-chipj\Desktop"),
    Action("copy", r"C:\Users\chipj\Pictures",
           "Pictures",
           dest=rf"{DEST_ROOT}\C-chipj\Pictures"),
    Action("copy", r"C:\Users\chipj\Music",
           "Music in user profile (separate from D:\\Music)",
           dest=rf"{DEST_ROOT}\C-chipj\Music"),
    Action("copy", r"C:\Users\chipj\Videos",
           "Videos",
           dest=rf"{DEST_ROOT}\C-chipj\Videos"),
    Action("copy", r"C:\Users\chipj\Saved Games",
           "Game saves",
           dest=rf"{DEST_ROOT}\C-chipj\Saved Games"),
    Action("copy", r"C:\Users\chipj\Contacts",
           "Contacts",
           dest=rf"{DEST_ROOT}\C-chipj\Contacts"),
    Action("copy", r"C:\Users\chipj\Favorites",
           "Browser bookmarks (legacy IE/Edge favorites)",
           dest=rf"{DEST_ROOT}\C-chipj\Favorites"),
    Action("skip", r"C:\Users\chipj\Downloads",
           "Disposable installers — confirmed deletable (Chip 2026-05-09)"),
    Action("copy", r"C:\Users\chipj\OneDrive",
           "Local OneDrive sync folder (the data, not the service)",
           dest=rf"{DEST_ROOT}\C-chipj\OneDrive"),
    Action("copy", r"C:\Users\chipj\Apple",
           "Apple/iCloud sync data",
           dest=rf"{DEST_ROOT}\C-chipj\Apple"),
    Action("copy", r"C:\Users\chipj\Intel",
           "Intel folder — review what this is post-copy",
           dest=rf"{DEST_ROOT}\C-chipj\Intel"),
    Action("copy", r"C:\Users\chipj\Muse Hub",
           "Muse Hub data (MuseScore/Muse Group)",
           dest=rf"{DEST_ROOT}\C-chipj\Muse Hub"),
    Action("copy", r"C:\Users\chipj\source",
           "Visual Studio source folder",
           dest=rf"{DEST_ROOT}\C-chipj\source"),

    # --- Critical dotfiles ---
    Action("skip", r"C:\Users\chipj\.ssh",
           "Confirmed not present + HTTPS-only on this machine (Chip 2026-05-10)"),
    Action("skip", r"C:\Users\chipj\.gnupg",
           "Confirmed not used on this machine (Chip 2026-05-10)"),
    Action("copy", r"C:\Users\chipj\.gitconfig",
           "Git global config",
           dest=rf"{DEST_ROOT}\C-chipj\.gitconfig"),
    Action("copy", r"C:\Users\chipj\.claude",
           "Claude Code config + memory + projects",
           dest=rf"{DEST_ROOT}\C-chipj\.claude"),
    Action("copy", r"C:\Users\chipj\.config",
           "XDG config home",
           dest=rf"{DEST_ROOT}\C-chipj\.config"),
    Action("copy", r"C:\Users\chipj\.vscode",
           "VSCode settings (extensions excluded — VSCode reinstalls them on first launch)",
           dest=rf"{DEST_ROOT}\C-chipj\.vscode",
           excludes=["extensions"]),
    Action("copy", r"C:\Users\chipj\.ipython",
           "IPython config",
           dest=rf"{DEST_ROOT}\C-chipj\.ipython"),
    Action("copy", r"C:\Users\chipj\.jupyter",
           "Jupyter config",
           dest=rf"{DEST_ROOT}\C-chipj\.jupyter"),

    # --- AppData: Roaming only (configs, license keys, signatures) ---
    Action("copy", r"C:\Users\chipj\AppData\Roaming",
           "AppData\\Roaming — app configs, license keys, signatures",
           dest=rf"{DEST_ROOT}\C-chipj\AppData\Roaming",
           excludes=APPDATA_CACHE_EXCLUDES),

    # --- Skip: Windows-only junk or replaceable caches ---
    Action("skip", r"C:\Users\chipj\3D Objects",
           "Windows-only useless folder"),
    Action("skip", r"C:\Users\chipj\Searches",
           "Windows-only saved-search shortcuts"),
    Action("skip", r"C:\Users\chipj\Links",
           "Windows-only quick-access shortcuts"),
    Action("skip", r"C:\Users\chipj\MicrosoftEdgeBackups",
           "Edge backups — bookmarks already covered by AppData\\Roaming"),
    Action("skip", r"C:\Users\chipj\AppData\Local",
           "AppData\\Local — caches and per-machine state, replaceable"),
    Action("skip", r"C:\Users\chipj\AppData\LocalLow",
           "AppData\\LocalLow — rare browser sandbox data, replaceable"),
    Action("skip", r"C:\Users\chipj\.android",
           "Android SDK cache + ADB keys (regenerable)"),
    Action("skip", r"C:\Users\chipj\.cache",
           "User cache directory — by definition replaceable"),
    Action("skip", r"C:\Users\chipj\.gradle",
           "Gradle build cache — replaceable"),
    Action("skip", r"C:\Users\chipj\.dotnet",
           ".NET SDK installs — reinstall on Linux"),
    Action("skip", r"C:\Users\chipj\.local",
           "XDG local data home — mostly app caches; review individually if you used something specific"),
    Action("skip", r"C:\Users\chipj\.matplotlib",
           "Matplotlib font cache — regenerated on first plot"),
    Action("skip", r"C:\Users\chipj\.dbus-keyrings",
           "D-Bus session keyrings — ephemeral"),
    Action("skip", r"C:\Users\chipj\.code-index",
           "Code search index — regenerated"),
    Action("skip", r"C:\Users\chipj\.pytinytex",
           "TinyTeX install — reinstall on Linux"),
    Action("skip", r"C:\Users\chipj\.templateengine",
           ".NET template engine cache"),
    Action("skip", r"C:\Users\chipj\.abjad",
           "Abjad/LilyPond cache"),
    Action("skip", r"C:\Users\chipj\.vs",
           "Visual Studio per-user cache"),
    Action("skip", r"C:\Users\chipj\.lilypond-fonts.cache-2",
           "LilyPond font cache — regenerable"),
    Action("skip", r"C:\Users\chipj\.Neo4jDesktop",
           "Neo4j Desktop install — confirmed not needed (Chip 2026-05-10)"),

    # ============================================================
    # C:\ top-level non-Users data
    # ============================================================
    Action("skip", r"C:\bin",
           "C:\\bin (just pathy.py) — confirmed deletable (Chip 2026-05-10)"),
    Action("skip", r"C:\Devices",
           "C:\\Devices — confirmed deletable (Chip 2026-05-10)"),

    # ============================================================
    # F:\Users — old user profile
    # ============================================================
    Action("copy", r"F:\Users\Chip",
           "Old 'Chip' user profile (Pictures + Voice Memos staged separately above for easy Phase B pickup)",
           dest=rf"{DEST_ROOT}\F-Chip",
           excludes=APPDATA_CACHE_EXCLUDES + ["Local", "LocalLow", ".cache", ".gradle"]),

    # --- Surface specific F: subdirs to staging roots for Phase B ---
    # Pictures: consolidate with master picture collection on E: NAS post-Linux
    Action("copy", r"F:\Users\Chip\Pictures",
           "F: pictures — staged separately for Phase B consolidation into master collection",
           dest=rf"{DEST_ROOT}\F-Chip-Pictures"),
    # Voice Memos: production-side placement on F: media drive (/srv/media/voice-memos)
    Action("copy", r"F:\Users\Chip\Music\iTunes\iTunes Media\Voice Memos",
           "F: iTunes Voice Memos (m4a) — important production-side audio for Chip",
           dest=rf"{DEST_ROOT}\F-voice-memos"),

    # ============================================================
    # F:\ top-level user data
    # ============================================================
    Action("copy", r"F:\_local.git",
           "Old git repos at F:\\_local.git",
           dest=rf"{DEST_ROOT}\F-_local.git"),
    Action("copy", r"F:\Chess Openings Files",
           "Chess opening files (hobby data)",
           dest=rf"{DEST_ROOT}\F-Chess Openings Files"),

    # ============================================================
    # F:\ — guitar pedal design files (mixed with install: copy whole tree)
    # ============================================================
    Action("copy", r"F:\Cadence",
           "Cadence (EDA) — guitar pedal design files mixed with install; whole tree (Chip 2026-05-10)",
           dest=rf"{DEST_ROOT}\F-Cadence"),
    Action("copy", r"F:\EAGLE-7.6.0",
           "Autodesk EAGLE — guitar pedal design files mixed with install; whole tree (Chip 2026-05-10)",
           dest=rf"{DEST_ROOT}\F-EAGLE-7.6.0"),

    # ============================================================
    # F:\ skips — installs / caches with no personal data
    # ============================================================
    Action("skip", r"F:\Peshka",
           "Chess engine install — confirmed deletable (Chip 2026-05-10)"),
    Action("skip", r"F:\SPB_Data",
           "Confirmed deletable (Chip 2026-05-10)"),
    Action("skip", r"F:\wdl-ol",
           "WDL-OL audio plugin SDK install — confirmed deletable (Chip 2026-05-10)"),
    Action("skip", r"F:\wf",
           "Confirmed deletable (Chip 2026-05-10)"),
    Action("skip", r"F:\PSFONTS",
           "PostScript fonts — replaceable, not personal"),
    Action("skip", r"F:\inetpub",
           "IIS web server data — replaceable, not personal"),
]
