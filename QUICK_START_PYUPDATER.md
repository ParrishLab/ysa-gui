# PyUpdater Quick Start

**TL;DR**: Replace the janky auto-update system with PyUpdater in 5 minutes.

## 1. Install & Setup (One-Time)

```bash
# Install PyUpdater
pip install -r src/helpers/update/requirements.txt

# Run interactive setup
./setup_pyupdater.sh

# Follow prompts, then paste public key into:
# src/helpers/update/Updater.py → CLIENT_CONFIG["PUBLIC_KEY"]
```

## 2. Test Locally

```bash
# Build and package
./test_pyupdater_build.sh

# Follow prompts to start local test server
```

## 3. Setup CI/CD (One-Time)

```bash
# Encode secrets
base64 -i .pyupdater/keypack.pyu  # Add to GitHub as PYUPDATER_KEYPACK
base64 -i .pyupdater/config.pyu   # Add to GitHub as PYUPDATER_CONFIG
```

Then update workflows following: `.github/workflows/PYUPDATER_CI_EXAMPLE.md`

## What You Get

- ✅ Delta updates (8-16x faster for small changes)
- ✅ Signature verification (secure)
- ✅ Auto-installation (no manual PKG/EXE opening)
- ✅ Progress indicators (download %)
- ✅ Background downloads (non-blocking)
- ✅ Automatic rollback on failure

## Files You Need to Know

- `src/helpers/update/Updater.py` - Main updater code
- `PYUPDATER_SETUP.md` - Detailed setup guide
- `AUTO_UPDATE_MIGRATION.md` - Full migration guide
- `.github/workflows/PYUPDATER_CI_EXAMPLE.md` - CI/CD integration

## Common Issues

**"No update available" when one exists**
- Check `PUBLIC_KEY` in `Updater.py` matches your keypack

**"Signature verification failed"**
- Public/private key mismatch
- Re-run `pyupdater keys --show` and update `Updater.py`

**CI/CD fails**
- Verify `PYUPDATER_KEYPACK` and `PYUPDATER_CONFIG` secrets are set
- Check they're base64 encoded correctly

## Need Help?

- Read: `PYUPDATER_SETUP.md` for detailed setup
- Read: `AUTO_UPDATE_MIGRATION.md` for migration details
- Visit: https://www.pyupdater.org/ for PyUpdater docs
