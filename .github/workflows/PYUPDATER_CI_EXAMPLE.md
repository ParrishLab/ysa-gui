# PyUpdater CI/CD Integration Guide

This document describes how to integrate PyUpdater into the existing CI/CD pipeline.

## Overview

The current build pipeline (`build-and-release.yml`) needs to be updated to:
1. Package the PyInstaller build with PyUpdater
2. Sign the package using stored keys
3. Upload to GitHub releases in PyUpdater format

## Required GitHub Secrets

Add these secrets to your GitHub repository:
- `PYUPDATER_KEYPACK`: Base64-encoded contents of `.pyupdater/keypack.pyu`
- `PYUPDATER_CONFIG`: Base64-encoded contents of `.pyupdater/config.pyu`

To create these secrets:

```bash
# From your local machine (after running setup_pyupdater.sh):
base64 -i .pyupdater/keypack.pyu

# Copy the output and add it as PYUPDATER_KEYPACK secret in GitHub

base64 -i .pyupdater/config.pyu

# Copy the output and add it as PYUPDATER_CONFIG secret in GitHub
```

## Modified Workflow Steps

### After PyInstaller Build

Add these steps after the "Build with PyInstaller" step in `shared-build.yml`:

```yaml
      - name: Restore PyUpdater config
        shell: bash
        run: |
          mkdir -p .pyupdater
          echo "${{ secrets.PYUPDATER_KEYPACK }}" | base64 -d > .pyupdater/keypack.pyu
          echo "${{ secrets.PYUPDATER_CONFIG }}" | base64 -d > .pyupdater/config.pyu

      - name: Package with PyUpdater (macOS)
        if: runner.os == 'macOS'
        run: |
          source venv/bin/activate  # or venv_x86/bin/activate for x86_64
          pyupdater pkg --process dist/YsaGUI.app --app-version ${{ steps.ver.outputs.version }}
          pyupdater pkg --sign

      - name: Package with PyUpdater (Windows)
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          .\venv\Scripts\Activate.ps1
          pyupdater pkg --process dist\YsaGUI --app-version ${{ steps.ver.outputs.version }}
          pyupdater pkg --sign
```

### Upload PyUpdater Artifacts

Replace the current artifact upload with:

```yaml
      - name: Upload PyUpdater Package (macOS)
        if: runner.os == 'macOS'
        uses: actions/upload-artifact@v4
        with:
          name: pyupdater-macos-${{ matrix.arch }}
          path: pyu-data/deploy/
          retention-days: ${{ inputs.artifact_retention_days }}

      - name: Upload PyUpdater Package (Windows)
        if: runner.os == 'Windows'
        uses: actions/upload-artifact@v4
        with:
          name: pyupdater-windows
          path: pyu-data/deploy/
          retention-days: ${{ inputs.artifact_retention_days }}
```

### Release Job

Update the release job in `build-and-release.yml`:

```yaml
  release:
    if: github.event_name == 'push'
    needs: [build]
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Download PyUpdater Artifacts
        uses: actions/download-artifact@v4
        with:
          path: pyu-artifacts

      - name: Read version from Constants.py
        id: release_ver
        shell: bash
        run: |
          version=$(grep -E '^__version__\s*=\s*["\x27]' src/helpers/Constants.py | sed -E 's/.*["\x27]([^"\x27]+)["\x27].*/\1/')
          if [ -z "$version" ]; then
            echo "Error: Could not extract version from Constants.py"
            exit 1
          fi
          echo "version=$version" >> $GITHUB_OUTPUT
          echo "tag=v$version" >> $GITHUB_OUTPUT
          echo "Version from Constants.py: $version"

      - name: Merge PyUpdater artifacts
        run: |
          mkdir -p deploy
          # Merge all PyUpdater deploy folders
          find pyu-artifacts -name "deploy" -type d -exec cp -r {}/* deploy/ \;

      - name: Create or Update Release
        uses: softprops/action-gh-release@v1
        with:
          token: ${{ github.token }}
          tag_name: ${{ steps.release_ver.outputs.tag }}
          name: Release ${{ steps.release_ver.outputs.version }}
          prerelease: false
          files: deploy/*
          fail_on_unmatched_files: true
          body: |
            ## YSA GUI ${{ steps.release_ver.outputs.version }}

            This release uses PyUpdater for secure, delta updates.

            ### Downloads
            The app will automatically detect and install updates.
            Manual downloads are also available in the release assets.

            Built from commit ${{ github.sha }}
```

## Alternative: Hybrid Approach

If you want to support both PyUpdater and manual downloads, you can:

1. Keep the existing PKG/EXE builds for manual installation
2. Add PyUpdater packages as additional release assets
3. Users with the app will get automatic updates via PyUpdater
4. New users can download the PKG/EXE manually

For this approach, keep both packaging methods in the CI/CD:

```yaml
      # Keep existing PKG/EXE creation
      - name: Prepare Package (macOS)
        run: |
          pkgbuild --root ... --identifier ...

      # Add PyUpdater packaging
      - name: Package with PyUpdater (macOS)
        run: |
          pyupdater pkg --process dist/YsaGUI.app --app-version ${{ steps.ver.outputs.version }}
          pyupdater pkg --sign

      # Upload both
      - name: Upload macOS Package
        uses: actions/upload-artifact@v4
        with:
          name: macos-package-${{ matrix.arch }}
          path: YSA_GUI_MacOS_${{ matrix.arch }}.pkg

      - name: Upload PyUpdater Package (macOS)
        uses: actions/upload-artifact@v4
        with:
          name: pyupdater-macos-${{ matrix.arch }}
          path: pyu-data/deploy/
```

## Testing the Pipeline

1. Create a test branch
2. Update the version in `src/helpers/Constants.py`
3. Push to trigger the workflow
4. Check that PyUpdater packages are created and uploaded
5. Download and test the update process locally

## Rollback Plan

If PyUpdater causes issues, you can quickly rollback:

1. Revert the `Updater.py` changes
2. Restore the old `UpdateThread.py`
3. Revert the `main.py` changes
4. Remove PyUpdater from CI/CD

The old PKG/EXE packages will still work for manual installation.

## Additional Notes

- PyUpdater packages are much smaller for incremental updates (only changed files)
- The first download is similar in size to the PKG/EXE
- Signature verification ensures security
- Updates are atomic - if extraction fails, the old version remains
- The app automatically restarts after successful update
