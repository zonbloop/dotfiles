Of course. Here is a summary of those steps, formatted for a README file.

-----

## Memento Mori Desktop Calendar Setup

These instructions will guide you through setting up the Memento Mori calendar scripts to automatically update your desktop wallpaper on a Linux system using systemd.

### 1\. Installation

First, you need to place the scripts in a local directory and make them executable.

1.  **Create a directory** for the scripts:

    ```bash
    mkdir -p ~/.local/share/memento_mori
    ```

2.  **Copy the scripts** into the newly created directory.

    ```bash
    # Replace 'path/to/' with the actual location of your downloaded files
    cp path/to/memento_mori.py ~/.local/share/memento_mori/
    cp path/to/update_wallpaper.sh ~/.local/share/memento_mori/
    ```

3.  **Make the scripts executable**:

    ```bash
    chmod +x ~/.local/share/memento_mori/memento_mori.py
    chmod +x ~/.local/share/memento_mori/update_wallpaper.sh
    ```

### 2\. Configuration & Manual Test

Before automating, make sure to configure the scripts and test them manually.

1.  **Edit the Python script** (`~/.local/share/memento_mori/memento_mori.py`) to set your birthdate and any other preferences.
2.  **Edit the shell script** (`~/.local/share/memento_mori/update_wallpaper.sh`) to ensure it uses the correct command to set the wallpaper for your specific desktop environment (e.g., for KDE Plasma, the command is `plasma-apply-wallpaperimage`).
3.  **Run a manual test** to generate the wallpaper and set it:
    ```bash
    # Generate the wallpaper image
    python3 ~/.local/share/memento_mori/memento_mori.py

    # Set the wallpaper
    ~/.local/share/memento_mori/update_wallpaper.sh
    ```
    Verify that your desktop wallpaper updates correctly.

### 3\. Automation with systemd

Next, set up the systemd timer to run the script automatically.

1.  **Create the systemd user directory**:

    ```bash
    mkdir -p ~/.config/systemd/user
    ```

2.  **Copy the service and timer files**:

    ```bash
    # Replace 'path/to/' with the actual location of your downloaded files
    cp path/to/memento-mori.service ~/.config/systemd/user/
    cp path/to/memento-mori.timer ~/.config/systemd/user/
    ```

    **Note:** If you used a different script location than `~/.local/share/memento_mori`, you must edit the `ExecStart` path inside `memento-mori.service`.

3.  **Enable and start the timer**:

    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now memento-mori.timer
    ```

### 4\. Verification (Optional)

You can check that the service and timer are running correctly.

  * **Check the timer schedule**:

    ```bash
    systemctl --user list-timers | grep memento
    ```

  * **Check the service status**:

    ```bash
    systemctl --user status memento-mori.service
    ```
