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
photo-import/
├── README.md
├── main.py
├── config.py
├── detect.py
├── mount.py
├── photo_copy.py
├── cleanup.py
├── .env.example
└── tests/
```

Uses shared modules from root:
- `lock`: Process locking via `lock/ProcessLock`
- `log`: Logging via `log/build_logger`
- `dotenv`: Environment variable loading via `dotenv/load_dotenv`

The unit tests for this script live under `photo-import/tests/`.

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

`photo_copy.py`
- Walk the mounted filesystem.
- Select files by configured extension set.
- Exclude thumbnails, caches, and preview files.
- Copy to the destination folder using standard-library utilities.

`cleanup.py`
- Centralize final unmount and state cleanup behavior.
- Make teardown idempotent.

## Configuration

The following items are configurable in `config.py`:

- `log_file`: Path to log file (default: `/var/log/photo-import.log`)
- `lock_file`: Path to lock file (default: `/tmp/photo-import.lock`)
- `mount_point`: Mount point for SD card (default: `/mnt/camera-sd-card`)
- `destination_root`: Destination for imported files
- `read_only`: Mount read-only (default: `True`)
- `allowed_extensions`: Supported file extensions
- `excluded_dir_names`: Directories to skip
- `excluded_file_names`: Files to skip
- `excluded_suffixes`: File suffixes to skip

All paths can be configured via environment variables. See `.env.example`.

## Operational Notes

- The script is expected to run with enough privileges to mount and unmount devices.
- Read-only mounting is the default for safety.
- The import step should preserve source data and must not mutate the SD card.
- Logging defaults to file output. Set `PHOTO_IMPORT_LOG_FILE` environment variable to configure.
- A process lock prevents concurrent runs when scheduled from cron.

## Usage

Run the script directly on the NAS:

```bash
python photo-import/main.py
```

The script expects root privileges because it mounts and unmounts block devices.

## Notes On Current Behavior

- Device discovery is based on `lsblk`.
- Candidate partitions are limited to configured filesystem types.
- The mounted card must contain at least one configured required directory such as `DCIM`.
- The copy step preserves the relative directory layout under the configured destination root.
- Existing destination files are skipped by default instead of overwritten.
