import asyncio

from checker import check_wallets


async def main() -> None:
    await check_wallets()


if __name__ == "__main__":
    asyncio.run(main=main())
