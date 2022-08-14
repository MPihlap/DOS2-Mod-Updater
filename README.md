# DOS2-Mod-Updater
Utility to automate the downloading of mods with frequent updates.
Comes prepackaged with configuration to download the Epic Encounters mod with Derpy Moa's and Pip's addons as well as the Norbyte script extender.

## How to use

Download the `mod_updater_v*.*.*.zip` file [from the Releases](https://github.com/MPihlap/DOS2-Mod-Updater/releases).
Extract the two files in your DOS II definitive edition bin folder (sth like "\steamapps\common\Divinity Original Sin 2\DefEd\bin").
Edit the `mod_updater_config.yaml` file to suit your needs.
By default, the mod updater is configured to download the latest versions of the script extender, Epic Encounters, Epip Encounters and Derpy Moas's addons.

### Configuring Steam to launch using the updater

1. Right click the game and open properties
2. Go to the general tab
3. Add the following to the launch options: `"FULL PATH TO GAME.EXE" %command%`
    * Full example: `"C:\Program Files (x86)\Steam\steamapps\common\Divinity Original Sin 2\DefEd\bin\mod_updater.exe" %command%`

Now when you launch the game from Steam, it will update your mods and then launch the game.


### Configuring the updater

To add new mods or change the options for existing ones, open the `mod_updater_config.yaml` file in a text editor.
Further instructions and examples can be found there.

## How to develop / run natively
0. Clone the repository
1. Install Python 3 (tested on 3.10)
2. `pip install -r requirements.txt`
3. Edit & run `mod_updater.py` at your leisure

## Notes

Executable was created using [auto-py-to-exe](https://pypi.org/project/auto-py-to-exe/).
