import gdown
import requests
from bs4 import BeautifulSoup
import yaml

from os import listdir, replace, rmdir, getcwd, remove
import logging
from abc import ABC, abstractmethod
import zipfile


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
        logging.warning(e)
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

    def __init__(self, url, force_update=False, filenames=None) -> None:
        super().__init__(force_update=force_update)
        self.url = url
        self.filenames = filenames

    def needs_update(self) -> bool:
        if self.force_update:
            return True
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


class EpicEncountersUpdater(FileExistUpdater):
    def __init__(self, url, force_update=False, filenames=None) -> None:
        super().__init__(url, force_update, filenames)

    def needs_update(self) -> bool:
        return super().needs_update()

    def update(self):
        return super().update()

    def download(self) -> bool:
        return download_file(self.url, zip=True)


class EpipUpdater(Updater):


    def __init__(self, url, force_update=False) -> None:
        super().__init__(force_update=force_update)
        self.url = url
        grab = requests.get(self.url)
        self.soup = BeautifulSoup(grab.text, 'lxml')


    def needs_update(self):
        if self.force_update:
            logging.info("Forcing update.")
            return True

        latest_epip_version = int(self.soup.find_all("h2")[0].get("id").split("-")[0][1:])
        logging.debug(f"latest_epip_version {latest_epip_version}")
        current_epip = [file for file in listdir() if file.startswith("Epip")]
        self.current_epip = current_epip
        if len(current_epip) == 0:
            logging.info("No existing Epip Encounters installation found, downloading latest ...")
            return True
        else:
            current_epip_version = int(current_epip[-1].split("_")[1].split(".")[0][1:])
            if current_epip_version < latest_epip_version:
                logging.info(f"Current Epip Encounters version {current_epip_version} outdated, downloading latest ...")
                return True
            else:
                logging.info(f"Current Epip Encounters version {current_epip_version} is up to date, no update necessary.")
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
            self.download()
            self.delete_old()


def set_loglevel(loglevel):
    if loglevel == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    elif loglevel == "INFO":
        logging.basicConfig(level=logging.INFO)


def main():

    current_dir = getcwd()
    if not current_dir.endswith("Divinity Original Sin 2 Definitive Edition\Mods"):
        logging.warning(f"Your current directory {current_dir} does not seem to be correct. The path should end with 'Divinity Original Sin 2 Definitive Edition\Mods'")
        logging.warning(f"Press ENTER to continue anyway, Ctrl+C to cancel.")
        input()

    with open("mod_updater_config.yaml", "r") as stream:
        try:
            params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error("Unable to parse yaml. Check your syntax.")
            logging.error(exc)
            exit(1)
    logging.debug(f"yaml contents {params}")
    global_settings = params["Global"]
    force_update_all = global_settings["force_update_all"]
    set_loglevel(global_settings["loglevel"])
    params.pop("Global")
    for mod in params:
        if mod == "EpipEncounters":
            mod_params = params[mod]
            force_update = mod_params["force_update"] or force_update_all
            url = mod_params["url"]
            updater = EpipUpdater(url, force_update=force_update)
            updater.update()
        elif mod == "EpicEncounters":
            mod_params = params[mod]
            force_update = mod_params["force_update"] or force_update_all
            url = mod_params["url"]
            filenames = mod_params["filenames"]
            updater = EpicEncountersUpdater(url, force_update, filenames=filenames)
            updater.update()
        else: # Generic mod downloader
            mod_params = params[mod]
            force_update = mod_params["force_update"] or force_update_all
            url = mod_params["url"]
            if "filenames" in mod_params.keys():
                filenames = mod_params["filenames"]
                updater = FileExistUpdater(url, force_update=force_update, filenames=filenames)
                updater.update()
            else:
                updater = NoBrainUpdater(url, force_update)
                updater.update()

if __name__ == "__main__":
    main()
