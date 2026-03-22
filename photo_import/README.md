# `photo-import`

`photo-import` automates importing photos and videos from a camera SD card inserted into the physical SD card slot on a TrueNAS machine.

## Goal

The workflow should be safe, dependency-free, and unattended:

1. Detect a suitable SD card.
2. Derive a stable device id from block-device metadata.
3. Mount the card under a managed mount root unless it is already mounted.
4. Copy supported media files into a per-device import destination.
4. Exclude thumbnails and preview artifacts.
5. Unmount the card even when failures occur.

If no suitable card is present, the script should exit without error.

## Non-Goals

- No GUI
- No external Python packages
- No database
- No always-on daemon requirement inside the script itself

If scheduling or triggering is needed, that should be handled by the NAS environment, not embedded deeply in the application logic.

## Layout

```text
photo_import/
├── README.md
├── main.py
├── config.py
├── detect.py
├── mount.py
├── photo_sync.py
├── cleanup.py
├── .photoignore
├── .env.example
└── tests/
```

Uses shared modules from `scriptlib`:
- `scriptlib.flockplus`: Process locking via `FileLock`
- `scriptlib.log`: Logging via `build_logger`
- `scriptlib.dotenv`: Environment variable loading via `load_dotenv`
- `scriptlib.pyrsync`: Media sync via system `rsync`

The unit tests for this script live under `photo_import/tests/`.

## Responsibilities

`main.py`
- Parse arguments if needed.
- Load configuration.
- Orchestrate detect -> mount -> copy -> unmount.
- Convert exceptions into clear exit codes and logs.

`config.py`
- Define all configurable paths and rules.
- Keep defaults in one place.
- Avoid scattering hard-coded values across modules.

`detect.py`
- Discover candidate removable devices and partitions.
- Identify likely camera SD cards.
- Return structured device information.

`mount.py`
- Mount the selected device read-only.
- Check whether the mount succeeded.
- Unmount reliably during cleanup.

`photo_sync.py`
- Walk the mounted filesystem and derive `rsync` filters.
- Select files by configured include/exclude patterns.
- Exclude thumbnails, caches, and preview files.
- Sync the selected media subset to the destination folder using `rsync`.

`cleanup.py`
- Centralize final unmount and state cleanup behavior.
- Make teardown idempotent.

## Configuration

The following items are configurable in `config.py`:

- `log_file`: Optional path to log file (default: stdout/stderr)
- `log_level`: Logging threshold such as `INFO` or `DEBUG` (default: `INFO`)
- `lock_file`: Path to lock file (default: `/tmp/photo-import.lock`)
- `mount_root`: Root directory for derived per-device mount paths (recommended: `/tmp/photo-import/mnt`)
- `import_root`: Root directory for derived per-device import paths
- `read_only`: Mount read-only (default: `True`)
- `excluded_patterns`: Include/exclude media patterns (loaded from `.photoignore`)

All paths can be configured via environment variables. See `.env.example`.

## Supported Media Patterns

The default media patterns are defined in `photo_import/.photoignore`.

Included image suffixes:
- `.jpg`, `.JPG`, `.jpeg`, `.JPEG`
- `.png`, `.PNG`
- `.heic`, `.HEIC`
- `.heif`, `.HEIF`
- `.arw`, `.ARW`
- `.cr2`, `.CR2`
- `.cr3`, `.CR3`
- `.nef`, `.NEF`
- `.dng`, `.DNG`
- `.raf`, `.RAF`
- `.rw2`, `.RW2`
- `.orf`, `.ORF`
- `.srw`, `.SRW`

Included video suffixes:
- `.mp4`, `.MP4`
- `.mov`, `.MOV`
- `.mts`, `.MTS`
- `.m2ts`, `.M2TS`
- `.avi`, `.AVI`
- `.mkv`, `.MKV`

Excluded by default:
- Thumbnail and preview artifacts such as `.thm`, `.THM`, `.thumb`
- Thumbnail/system directories matching patterns like `*THUMBNAILS*`, `*thumb*`, `*Spotlight*`, and `*@eaDir*`

## Operational Notes

- The script is expected to run with enough privileges to mount and unmount devices.
- Read-only mounting is the default for safety.
- The import step should preserve source data and must not mutate the SD card.
- Logging defaults to stdout/stderr. Set `PHOTO_IMPORT_LOG_FILE` to a file path if you want file logging.
- Set `PHOTO_IMPORT_LOG_LEVEL=DEBUG` to log why each block device is accepted or rejected during detection.
- A process lock prevents concurrent runs when scheduled from cron.
- `rsync` is required on the host system for media sync.
- The recommended mount root is `/tmp/photo-import/mnt` so script-created mountpoints live on tmpfs instead of under `/mnt`.
- Empty mount directories created under that root are intentionally left in place; the script does not perform explicit mount-path cleanup.

## Usage

Run the script from the repository root entrypoint on the NAS:

```bash
python3 /mnt/tank/script/run.py photo_import
```

This entrypoint is intended to be stable for cron-style execution where the working directory is unknown.

To verify the repo entrypoint and imports without running the script logic:

```bash
python3 /mnt/tank/script/run.py importcheck
```

The script expects root privileges because it mounts and unmounts block devices.

## Notes On Current Behavior

- Device discovery is based on `lsblk`.
- Device ids are derived from ordered metadata parts: model, serial, filesystem type, UUID, and PARTUUID.
- Candidate partitions are limited to configured filesystem types.
- The mounted card must contain at least one configured required directory such as `DCIM`.
- The sync step uses `rsync` with generated include/exclude rules to mirror the selected media subset.
- Extra files in destination are deleted to make destination match source.
- Existing destination files that are already identical are skipped by `rsync`.
- If a candidate device is already mounted, its existing mountpoint is reused instead of remounting it.
