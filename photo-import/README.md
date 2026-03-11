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
├── copy.py
├── cleanup.py
└── logging_utils.py
```

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

`copy.py`
- Walk the mounted filesystem.
- Select files by configured extension set.
- Exclude thumbnails, caches, and preview files.
- Copy to the destination folder using standard-library utilities.

`cleanup.py`
- Centralize final unmount and state cleanup behavior.
- Make teardown idempotent.

`logging_utils.py`
- Provide lightweight file and console logging helpers.
- Keep logging format consistent.

## Configuration

The following items should be configurable in `config.py`:

- `mount_point`
- `destination_root`
- `log_file`
- `state_file`
- `read_only`
- `allowed_extensions`
- `excluded_dir_names`
- `excluded_file_names`
- `excluded_suffixes`

Initial examples for file selection:
- Allowed media extensions: `.jpg`, `.jpeg`, `.png`, `.heic`, `.arw`, `.cr2`, `.cr3`, `.nef`, `.dng`, `.raf`, `.rw2`, `.orf`, `.mp4`, `.mov`, `.mts`, `.m2ts`, `.avi`
- Common exclusions: `.thm`, `thumb`, `thumbnails`, `@eadir`

These are examples only. The code should treat them as configuration, not policy hard-coded into business logic.

## Operational Notes

- The script is expected to run with enough privileges to mount and unmount devices.
- Read-only mounting is the default for safety.
- The import step should preserve source data and must not mutate the SD card.
- Logging should make it obvious which device was detected, where files were copied, and whether unmount succeeded.

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
