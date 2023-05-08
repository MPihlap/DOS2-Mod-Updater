import re
import gdown
import requests
from bs4 import BeautifulSoup
import yaml

import os, sys
from os import getcwdb, listdir, replace, rmdir, getcwd, remove, chdir, environ
from os.path import exists, dirname
import logging
from abc import ABC, abstractmethod
import zipfile
import subprocess
from pathlib import Path
import time
import datetime
import json
import errno


def move_contents_here(folder):
    """
    Move files from target folder to current path.

    """
    for file in listdir(folder):
        replace(f"{folder}/{file}", file)



def download_file(url, target_filename=None, zip=False):
    try:
        if url.startswith("https://drive.google.com/"):
            if "folder" in url:
                gdown.download_folder(url, quiet=False, output="temp_folder")
                move_contents_here("temp_folder")
                rmdir("temp_folder")
            else:
                if zip:
                    gdown.download(url, output="temp_zip.zip", quiet=False, fuzzy=True)
                    with zipfile.ZipFile("temp_zip.zip", 'r') as zip_ref:
                        members = zip_ref.namelist()
                        logging.debug(f"members in zip {members}")
                        zip_ref.extractall()
                    remove("temp_zip.zip")
                    if members[0][-1] == "/": # If files are nested in a folder, get them out
                        move_contents_here(members[0])
                        rmdir(members[0])
                else:
                    gdown.download(url, quiet=False, output=target_filename, fuzzy=True)
        else:
            get_response = requests.get(url,stream=True)
            file_name = url.split("/")[-1] if target_filename is None else target_filename
            with open(file_name, 'wb') as f:
                for chunk in get_response.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
            if zip:
                with zipfile.ZipFile(file_name, 'r') as zip_ref:
                    zip_ref.extractall()
                remove(file_name)
        return True
    except Exception as e:
        logging.exception(e)
        logging.warning(f"Downloading url {url} unsuccessful.")
        return False


class Updater(ABC):

    def __init__(self, force_update=False) -> None:
        super().__init__()
        self.force_update = force_update

    @abstractmethod
    def needs_update(self) -> bool:
        """
            Check if current version of mod is already up to date.

            return: bool
        """
        return True


    @abstractmethod
    def download(self) -> bool:
        """
            Download all necessary files.

            return: bool, was downloading successful or not.
        """
        return


    def update(self):
        if self.needs_update():
            self.download()


class FileExistUpdater(Updater):
    # Only checks if file exists.

    def __init__(self, url, force_update=False, filenames=[], metafiles=[]) -> None:
        super().__init__(force_update=force_update)
        self.url = url
        self.filenames = filenames
        self.metafiles = metafiles

    def needs_update(self) -> bool:
        if self.force_update:
            return True
        for metafile in self.metafiles:
            if exists(metafile): # If metafile exists, never update
                logging.warn(f"Found metafile at {metafile}, not updating")
                return False
        local_files = listdir()
        logging.debug(f"local files: {local_files}")
        for file in self.filenames:
            if file not in local_files:
                return True

        return False


    def update(self):
        return super().update()


    def download(self) -> bool:
        return download_file(self.url)


class FileTimestampUpdater(FileExistUpdater):
    # Checks if file exists and if it is older than the cloud version
    def __init__(self, url, force_update=False, filenames=None, cloud_version_dict=None, local_version_dict=None, metafiles=[]) -> None:
        super().__init__(url, force_update, filenames)
        self.cloud_version_dict = cloud_version_dict
        self.local_version_dict = local_version_dict
        self.metafiles = metafiles


    def is_file_outdated(self, filename, date):
        u_time = time.mktime(datetime.datetime.strptime(date, "%d/%m/%Y").timetuple())
        file_time = os.path.getmtime(filename)
        return u_time > file_time


    def is_version_outdated(self):
        if len(self.local_version_dict) == 0:
            return True # if there is no entry, assume an update is necessary

        return int(self.cloud_version_dict["Version"]) > int(self.local_version_dict["Version"])


    def needs_update(self) -> bool:
        if self.force_update:
            return True

        for metafile in self.metafiles:
            if exists(metafile): # If metafile exists, don't update
                logging.warn(f"Found metafile at {metafile}, not updating")
                return False

        # If files don't exist, update is necessary
        if super().needs_update():
            return True

        # If files are outdated, update is necessary
        for filename in self.filenames:
            if self.is_file_outdated(filename, self.cloud_version_dict["Date"]) or self.is_version_outdated():
                return True

        return False

    def update(self):
        if self.needs_update():
            if self.download():
                self.local_version_dict["Version"] = self.cloud_version_dict["Version"]
                self.local_version_dict["Date"] = self.cloud_version_dict["Date"]


class NoBrainUpdater(Updater):
    # Download the file, no questions asked. Used when no filenames are specified in the config.

    def __init__(self, url, force_update=False) -> None:
        super().__init__(force_update=force_update)
        self.url = url

    def needs_update(self) -> bool:
        return True


    def update(self):
        return super().update()


    def download(self) -> bool:
        return download_file(self.url)


class EpicEncountersUpdater(FileTimestampUpdater):
    def __init__(self, url, force_update=False, filenames=None, cloud_version_dict=None, local_version_dict=None, metafiles=[]) -> None:
        super().__init__(url, force_update, filenames, cloud_version_dict=cloud_version_dict, local_version_dict=local_version_dict, metafiles=metafiles)

    def needs_update(self) -> bool:
        return super().needs_update()

    def update(self):
        return super().update()

    def download(self) -> bool:
        return download_file(self.url, zip=True)


class EpipUpdater(Updater):


    def __init__(self, url, force_update=False, metafiles=[], cloud_version_dict=None, local_version_dict=None) -> None:
        super().__init__(force_update=force_update)
        self.url = url
        grab = requests.get(self.url)
        self.soup = BeautifulSoup(grab.text, 'html.parser')
        self.metafiles = metafiles
        self.current_epip = []
        self.cloud_version_dict = cloud_version_dict
        self.local_version_dict = local_version_dict

    def needs_update(self):
        if self.force_update:
            logging.info("Forcing update.")
            return True
        for metafile in self.metafiles:
            if exists(metafile): # If metafile exists, never update
                logging.warn(f"Found metafile at {metafile}, not updating")
                return False

        latest_epip_version = int(self.cloud_version_dict["Version"])
        logging.debug(f"latest_epip_version {latest_epip_version}")
        current_epip = [file for file in listdir() if file.startswith("EpipEncounters")]
        self.current_epip = current_epip
        if len(current_epip) == 0:
            logging.info("No existing Epip Encounters installation found, downloading latest ...")
            return True
        else:
            if len(self.local_version_dict) != 0:
                current_epip_version = int(self.local_version_dict["Version"])
            else:
                expression = '^EpipEncounters_v?(?P<Version>\d+)\.pak$'
                match = re.match(expression, current_epip[-1])
                if match is None:
                    logging.warning("Unable to detect version of local Epip file, forcing update")
                    return True
                current_epip_version = int(match.group("Version"))
            if current_epip_version < latest_epip_version:
                logging.debug(f"Current Epip Encounters version {current_epip_version} outdated, downloading latest ...")
                return True
            else:
                logging.debug(f"Current Epip Encounters version {current_epip_version} is up to date, no update necessary.")
                return False


    def download(self) -> bool:
        link = [link for link in self.soup.find_all("a") if "Download here" in link][0].get("href")
        logging.debug(f"link {link}")
        return download_file(link)

    def delete_old(self):
        for file in self.current_epip:
            remove(file)

    def update(self):
        if self.needs_update():
            download_success = self.download()
            if download_success:
                self.delete_old()
                self.local_version_dict["Version"] = self.cloud_version_dict["Version"]
                self.local_version_dict["Date"] = self.cloud_version_dict["Date"]


class ScriptExtenderUpdater(FileExistUpdater):
    def __init__(self, url, force_update=False, filenames=[], metafiles=[], config=None) -> None:
        super().__init__(url, force_update, filenames, metafiles)
        self.config = config

    def download(self) -> bool:
        grab = requests.get(self.url)
        soup = BeautifulSoup(grab.text, "html.parser")
        link = soup.find("a", href=True, text="from here").get("href")
        download_success = download_file(link, zip=True)
        if download_success:
            json_object = json.dumps(self.config, indent=4)
            # Writing to sample.json
            with open(self.filenames[0], "w") as outfile:
                outfile.write(json_object)
            return True
        else:
            return False


def get_metafile(executable, metafile):
    game_folder = Path(executable).parents[1] # navigate to main game folder
    logging.debug(f"game_folder {game_folder}")
    metafile_path = f"{game_folder.absolute()}{metafile}"
    return metafile_path


def set_loglevel(loglevel):
    if loglevel == "DEBUG":
        logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("mod_updater_debug.log", mode="w"),
            logging.StreamHandler()
        ])
    elif loglevel == "INFO":
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    else:
        error = ValueError(f"Incorrect debug level specified in yaml: {loglevel}. Please choose either DEBUG or INFO")
        logging.exception(error)
        input("Press ENTER to exit")
        exit(1)


def print_title():
    print(r"""    ____   ____  _____ ___      __  ___ ____   ____     __  __ ____   ____   ___   ______ ______ ____
   / __ \ / __ \/ ___/|__ \    /  |/  // __ \ / __ \   / / / // __ \ / __ \ /   | /_  __// ____// __ \
  / / / // / / /\__ \ __/ /   / /|_/ // / / // / / /  / / / // /_/ // / / // /| |  / /  / __/  / /_/ /
 / /_/ // /_/ /___/ // __/   / /  / // /_/ // /_/ /  / /_/ // ____// /_/ // ___ | / /  / /___ / _, _/
/_____/ \____//____//____/  /_/  /_/ \____//_____/   \____//_/    /_____//_/  |_|/_/  /_____//_/ |_|
                                                                                                      """)
    print(r"""                   __          __  ___      __
                  / /  __ __  /  |/  /___  / /___
                 / _ \/ // / / /|_/ // -_)/ /(_-<
                /_.__/\_, / /_/  /_/ \__//_//___/
                     /___/                       """)


def main():
    print_title()

    if getattr(sys, 'frozen', False):
        start_dir = dirname(sys.executable)
    else:
        start_dir = dirname(os.path.abspath(__file__))
    chdir(start_dir) # Move to defed bin folder, if not executing script from there
    if not start_dir.endswith('Divinity Original Sin 2\DefEd\\bin'):
        print(f"Your current directory {start_dir} does not seem to be correct. The path should end with 'Divinity Original Sin 2\DefEd\\bin'")
        print(f"Press ENTER to continue anyway, Ctrl+C to cancel.")
        input()

    try:
        with open("mod_updater_config.yaml", "r") as stream:
            try:
                params = yaml.safe_load(stream) # Throws yaml parse error
            except yaml.YAMLError as exc:
                raise yaml.YAMLError("Unable to parse yaml. Check your syntax.")
    except FileNotFoundError as e:
        logging.exception(e)
        logging.error("Please make sure the mod_updater_config.yaml file is in the same folder as the mod_updater.exe")
        input("Press ENTER to exit")
        exit(1)

    global_settings = params["Global"]
    force_update_all = global_settings["force_update_all"]
    loglevel = global_settings["loglevel"]
    set_loglevel(loglevel)

    logging.debug(f"yaml contents {params}")

    executable = global_settings["executable"]
    mod_folder = global_settings["mod_folder"]
    if "%UserProfile%" in mod_folder:
        mod_folder = mod_folder.replace("%UserProfile%", environ["USERPROFILE"])
        if not exists(mod_folder):
            onedrive_mod_folder = mod_folder.replace("Documents", os.path.join("OneDrive", "Documents"))
            print(onedrive_mod_folder)
            if exists(onedrive_mod_folder):
                mod_folder = onedrive_mod_folder
            else:
                e = FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), mod_folder)
                logging.exception(e)
                logging.error(f"Unable to locate mod folder! Make sure it is configured correctly in the mod_updater_config.yaml file.")
                input("Press ENTER to exit")
                exit(1)

    autorun = global_settings["autorun"]

    versions_url = global_settings["versions_url"]
    grab = requests.get(versions_url)
    cloud_versions = json.loads(grab.text)["Mods"]
    try:
        with open("local_versions.json") as file:
            local_versions = json.load(file)
    except FileNotFoundError:
        logging.warning("Local version file not found. Creating new file.")
        local_versions = {"Mods":{}}
    params.pop("Global")
    try:
        chdir(mod_folder)
        for mod in params:
            mod_params = params[mod]
            force_update = mod_params["force_update"] or force_update_all
            url = mod_params["url"]
            cloud_version_dict = cloud_versions.get(mod)

            local_version_dict = local_versions["Mods"].get(mod)
            if local_version_dict is None and cloud_version_dict is not None:
                logging.debug("Creating new local entry for {mod}")
                local_versions["Mods"][mod] = {}
                local_version_dict = local_versions["Mods"].get(mod)
            filenames = mod_params.get("filenames", [])
            metafiles = mod_params.get("metafiles", []) # Optional params
            for i, metafile in enumerate(metafiles):
                metafiles[i] = get_metafile(start_dir, metafile)

            if mod == "ScriptExtender":
                chdir(start_dir)
                config = mod_params["config"]
                updater = ScriptExtenderUpdater(url, force_update=force_update, filenames=filenames, metafiles=metafiles, config=config)
                updater.update()
                chdir(mod_folder)
                continue
            elif mod == "EpipEncounters":
                updater = EpipUpdater(url, force_update=force_update, metafiles=metafiles, cloud_version_dict=cloud_version_dict, local_version_dict=local_version_dict)
            elif mod == "EpicEncounters":
                updater = EpicEncountersUpdater(url, force_update=force_update, filenames=filenames, cloud_version_dict=cloud_version_dict, local_version_dict=local_version_dict, metafiles=metafiles)
            elif mod == "Derpy":
                updater = FileTimestampUpdater(url, force_update=force_update, filenames=filenames, cloud_version_dict=cloud_version_dict, local_version_dict=local_version_dict, metafiles=metafiles)
            else: # Generic mod downloader
                if len(filenames):
                    updater = FileExistUpdater(url, force_update=force_update, filenames=filenames, metafiles=metafiles)
                else:
                    updater = NoBrainUpdater(url, force_update)
            updater.update()
    except Exception as e:
        logging.exception(e)
        input("Press ENTER to exit")
        exit(1)

    chdir(start_dir)
    with open("local_versions.json", "w") as file:
        json_object = json.dumps(local_versions, indent=4)
        file.write(json_object)

    if autorun:
        if exists(executable):
            subprocess.Popen([executable])
        else:
            logging.error(f"Tried to run the game, but the path '{executable}' is not correct. Edit the mod_updater_config.yaml file to setup autorun.")
            input("Press ENTER to exit")
            exit(1)

if __name__ == "__main__":
    main()
