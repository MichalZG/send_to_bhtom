import argparse
import glob
import astropy.io.fits as fits
import os
import requests
import logging
import yaml
from yaml.loader import SafeLoader


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("./debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger()

CONFIG_FILE_PATH = "./config.yaml"
NAMES_MAP_FILE_PATH = "./names_map.yaml"


def read_yaml(path):
    with open(path) as f:
        data = yaml.load(f, Loader=SafeLoader)
    return data


def check_hashtag(config):
    if not "bhtom_hashtag" in config or config["bhtom_hashtag"] is None:
        hashtag = os.getenv("bhtom_hashtag")
        if hashtag is None:
            raise ValueError(
                "No hashtag found in either the configuration or the environment"
            )
        else:
            config["bhtom_hashtag"] = hashtag

    return config


def prepare_files_dict(files_list, config, names_map):
    files_dict = {}

    for file_path in files_list:

        file_filter = fits.getheader(file_path)[config["filter_key"]].strip()
        file_object = fits.getheader(file_path)[config["object_key"]].strip()

        if names_map and file_object in names_map.keys():
            file_object = names_map[file_object]

        if config["filter_map"] and file_filter in config["filter_map"].keys():
            file_filter = config["filter_map"][file_filter]

        files_dict[file_path] = {
            "filter": file_filter,
            "object": file_object,
        }

    return files_dict


def send_fits_file(files_dict, config, dry_run):
    logger.info(f"Sending.... \n")

    for file_path, file_data in files_dict.items():
        logger.info(f"Sending {file_path}")
        logger.info(f"File data: {file_data}")

        with open(os.path.join(file_path), "rb") as f:
            response = requests.post(
                url=config["bhtom_url"],
                headers={
                    "hashtag": config["hashtag"],
                },
                data={
                    "target": file_data["object"],
                    "data_product_type": "fits_file",
                    "matching_radius": str(config["radius"]),
                    "filter": file_data["filter"],
                    "dry_run": dry_run,
                },
                files={"files": f},
            )

        server_response = response.status_code
        logger.info(f"Server response: {response.text}, {server_response}")
        logger.info("-" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="uz send to bhtom", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        help="directory containing FITS images or a PHOT filepath",
        required=True,
    )
    parser.add_argument(
        "-p", "--pattern", type=str, help="pattern object name", default="*.fits"
    )
    parser.add_argument(
        "--dryrun",
        help="sends data, but does not store datapoints in BHTOM database",
        action="store_true",
    )
    args = parser.parse_args()

    dry_run = True if args.dryrun else False

    indir = os.path.join(str(args.dir), str(args.pattern))
    files_list = sorted(glob.glob(indir))

    files_list_str = "\n".join(files_list)
    logger.info(f"Files to send:\n{files_list_str}")
    logger.info("START PROCESSING........")

    config = read_yaml(CONFIG_FILE_PATH)
    names_map = read_yaml(NAMES_MAP_FILE_PATH)

    config = check_hashtag(config)

    files_dict = prepare_files_dict(files_list, config, names_map)
    send_fits_file(files_dict, config, dry_run)
