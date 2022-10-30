# DOS2-Mod-Updater
Utility to automate the downloading of mods with frequent updates.
Comes prepackaged with configuration to download the Epic Encounters mod with Derpy Moa's and Pip's addons as well as the Norbyte script extender.

## How to use

Download the `mod_updater_v*.*.*.zip` file [from the Releases](https://github.com/MPihlap/DOS2-Mod-Updater/releases).
Extract the two files in your DOS II definitive edition bin folder (sth like "\steamapps\common\Divinity Original Sin 2\DefEd\bin").
Edit the `mod_updater_config.yaml` file to suit your needs.
By default, the mod updater is configured to download the latest versions of the script extender, Epic Encounters, Epip Encounters and Derpy Moa's addons.

### Configuring Steam to launch using the updater

1. Right click the game and open properties
2. Go to the general tab
3. Add the following to the launch options: `"FULL PATH TO GAME.EXE" %command%`
    * Full example: `"C:\Program Files (x86)\Steam\steamapps\common\Divinity Original Sin 2\DefEd\bin\mod_updater.exe" %command%`

Now when you launch the game from Steam, it will update your mods and then launch the game.

### Configuring the updater

To add new mods or change the options for existing ones, open the `mod_updater_config.yaml` file in a text editor.
Further instructions and examples can be found there.

### Common issues and how to solve them

#### Version mismatch / can't build story / etc..

This generally means that something went wrong with detecting the latest versions of the mod and they are out of sync.
You can bruteforce your mods to update to the latest available version by setting the `force_update_all` parameter to `True` in the `mod_updater_config.yaml` file.
Once fixed, set it back to `False` to resume normal workings of the updater.

#### Epip features are broken

Could be that they are simply broken, but the issue can often be the script extender.
Make sure the script extender is using the `Release` update channel in the `mod_updater_config.yaml` file.
If it is set to `Devel`, set it to `Release`, delete the `ScriptExtenderUpdaterConfig.json` file and run the mod updater again.

#### Unable to locate mod folder

The updater does its best to auto-detect your DOSII mods folder.
On some occasions, its best is not enough.
If this happens, edit the `mod_updater_config.yaml` file and replace the `mod_folder` parameter with your actual mod folder.


## How to develop / run natively
0. Clone the repository
1. Install Python 3 (tested on 3.10)
2. `pip install -r requirements.txt`
3. Edit & run `mod_updater.py` at your leisure
