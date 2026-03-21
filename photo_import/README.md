# `photo-import`

`photo-import` automates importing photos and videos from a camera SD card inserted into the physical SD card slot on a TrueNAS machine.

## Goal

The workflow should be safe, dependency-free, and unattended:

1. Detect a suitable SD card.
2. Mount the card as read-only.
3. Copy supported media files to a configured destination.
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
├── .photoextensions
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
- Select files by configured extension set.
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
- `mount_point`: Mount point for SD card (default: `/mnt/camera-sd-card`)
- `destination_root`: Destination for imported files
- `read_only`: Mount read-only (default: `True`)
- `allowed_extensions`: Supported file extensions (loaded from `.photoextensions`)
- `excluded_dir_names`: Directories to skip (loaded from `.photoignore`)
- `excluded_file_names`: Files to skip
- `excluded_suffixes`: File suffixes to skip (loaded from `.photoignore`)

All paths can be configured via environment variables. See `.env.example`.

## Operational Notes

- The script is expected to run with enough privileges to mount and unmount devices.
- Read-only mounting is the default for safety.
- The import step should preserve source data and must not mutate the SD card.
- Logging defaults to stdout/stderr. Set `PHOTO_IMPORT_LOG_FILE` to a file path if you want file logging.
- Set `PHOTO_IMPORT_LOG_LEVEL=DEBUG` to log why each block device is accepted or rejected during detection.
- A process lock prevents concurrent runs when scheduled from cron.
- `rsync` is required on the host system for media sync.

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
- Candidate partitions are limited to configured filesystem types.
- The mounted card must contain at least one configured required directory such as `DCIM`.
- The sync step uses `rsync` with generated include/exclude rules to mirror the selected media subset.
- Extra files in destination are deleted to make destination match source.
- Existing destination files that are already identical are skipped by `rsync`.
