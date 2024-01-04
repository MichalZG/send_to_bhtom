import os
import requests
import argparse
import logging
import glob


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("./debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger()


BHTOM_URL = "https://uploadsvc2.astrolabs.pl/upload/"


def fill_data(args):
    data = {
        "target": args.object_name,
        "matching_radius": args.radius,
        "filter": args.filter,
        "data_product_type": args.data_product_type,
        "radius": args.radius,
        "observatory": args.observatory_name,
    }
    if args.observer:
        data["observer"] = args.observer
    if args.mjd:
        data["mjd"] = args.mjd
    if args.no_plot:
        data["no_plot"] = "True"
    if args.dry_run:
        data["dry_run"] = "True"
    if args.comment:
        data["comment"] = args.comment
    
    logger.info(f"Request configuration:{data}\n")
    return data


def send_fits_file(files_list, args):
    logger.info(f"Preparing request configuration.")
    data = fill_data(args)
    logger.info(f"Sending.... \n")

    for file_path in files_list:
        logger.info(f"Sending {file_path}")

        with open(os.path.join(file_path), "rb") as f:
            response = requests.post(
                url=BHTOM_URL,
                headers={"Authorization": f"Token {str(args.token)}"},
                data=data,
                files={"files": f},
            )

        server_response = response.status_code
        logger.info(f"Server response: {response.text}, {server_response}")
        logger.info(f"{'-' * 40}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="send to bhtom", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        help="directory containing FITS images or a PHOT filepath",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--pattern",
        type=str,
        help="pattern object name",
        default="*.fits",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--object_name",
        type=str,
        help="Object name",
        required=True,
    )
    parser.add_argument(
        "-f",
        "--filter",
        help="Filter name",
        default="GaiaSP/any",
    )
    parser.add_argument(
        "-t",
        "--token",
        type=str,
        help="""API token If not provided taken from env variable 'TOKEN'. 
                To set env variable run `EXPORT TOKEN=<your_hash>'""",
        default=os.environ.get("TOKEN"),
    )
    parser.add_argument(
        "--data_product_type",
        type=str,
        help="Data product type",
        default="fits_file",
    )
    parser.add_argument(
        "--observer",
        type=str,
        help="Observer name, optional",
        default=None,
    )
    parser.add_argument(
        "--observatory_name",
        default="",
        help="Observatory/Facility name to which this datapoint will be associated.",
    )
    parser.add_argument(
        "--mjd",
        type=str,
        help="Modified Julian Date (float) [note MJD=JD-2400000.5], optional",
        default=None,
    )
    parser.add_argument(
        "--radius",
        type=str,
        help="Radius, default=2",
        default="2",
    )
    parser.add_argument(
        "--dry_run",
        help="sends data, but does not store datapoints in BHTOM database",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no_plot",
        help="If true, the script will be run in Dry Run (test) mode. The data will processed but will not be stored in the database. The default is false.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--comment",
        default=None,
        help="Comment about the observation, data processing, etc.",
    )

    args = parser.parse_args()

    if args.token is None:
        raise ValueError("No token found. Check -h for help.")

    indir = os.path.join(str(args.dir), str(args.pattern))
    files_list = sorted(glob.glob(indir))
    files_list_str = "\n".join(files_list)

    logger.info(f"Files to send:\n{files_list_str}")
    logger.info("START PROCESSING........")

    send_fits_file(files_list, args)
