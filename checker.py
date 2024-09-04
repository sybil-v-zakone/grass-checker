import csv
from itertools import zip_longest
from typing import Optional

import aiohttp
from aiohttp_proxy import ProxyConnector
from loguru import logger
from tabulate import tabulate
from termcolor import cprint

URL = "https://api.getgrass.io/airdropAllocations?input=%7B%22walletAddress%22:%225{}%22%7D"
PROXIES_FILE_PATH = "data/proxies.txt"
ADDRESSES_FILE_PATH = "data/addresses.txt"
EXPORT_FILE_PATH = "data/result.csv"


def export_to_csv(file_path: str, headers: list, data: list) -> None:
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

    logger.info(f"Data has been exported to {file_path}")


def read_file_lines(file_path: str) -> list[str]:
    with open(file=file_path, mode="r") as file:
        return [line.strip() for line in file]


async def send_get_request(url: str, proxy: Optional[str] = None) -> ...:
    async with aiohttp.ClientSession(connector=get_proxy_connector(proxy=proxy)) as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Request failed with status: {response.status}")
                return None


def get_proxy_connector(proxy: Optional[str]) -> Optional[ProxyConnector]:
    if proxy:
        proxy_url = f"http://{proxy}"
        return ProxyConnector.from_url(url=proxy_url)
    return None


async def is_eligible(wallet_address: str, proxy: Optional[str]) -> bool:
    try:
        response = await send_get_request(
            url=URL.format(wallet_address),
            proxy=proxy,
        )
    except Exception as e:
        logger.exception(f"{wallet_address} Request failed: {e}")
        return False

    if response is None:
        logger.error(f"Status code was not 200, skipping wallet: {wallet_address}")
        return False

    result = response.get("result")

    if result is None:
        logger.error(f"Wallet {wallet_address} is not eligible")
        return False

    if isinstance(result, dict) and not result:
        logger.error(f"Wallet {wallet_address} is not eligible")
        return False

    return True


async def check_wallets() -> None:
    addresses = read_file_lines(ADDRESSES_FILE_PATH)
    proxies = read_file_lines(PROXIES_FILE_PATH)

    results = []

    for address, proxy in zip_longest(addresses, proxies):
        status = await is_eligible(wallet_address=address, proxy=proxy)
        results.append([address, "Yes" if status else "No"])

    headers = ["Address", "Is eligible"]

    cprint(tabulate(tabular_data=results, headers=headers, tablefmt="pretty"), color="red")
    export_to_csv(file_path=EXPORT_FILE_PATH, headers=headers, data=results)
