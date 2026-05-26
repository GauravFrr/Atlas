"""Quick OSM scanner smoke test."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from config import get_settings
from modules.lead_finder.scanners.osm_maps import OSMMapsScanner, _geocode_bbox, OVERPASS_URL, _user_agent


async def main() -> None:
    settings = get_settings()
    ua = _user_agent(settings)
    async with httpx.AsyncClient(timeout=60.0) as client:
        bb = await _geocode_bbox(client, "Austin TX", settings)
        print("bbox:", bb, "ua:", ua[:60])
        if not bb:
            return
        s, w, n, e = bb
        query = f"""
        [out:json][timeout:45];
        (
          node["amenity"="restaurant"]({s},{w},{n},{e});
        );
        out center 10;
        """
        resp = await client.post(
            OVERPASS_URL, data={"data": query}, headers={"User-Agent": ua}
        )
        print("overpass status:", resp.status_code)
        data = resp.json()
        print("elements:", len(data.get("elements", [])))
        for el in data.get("elements", [])[:3]:
            print(" -", el.get("tags", {}).get("name"))

    scanner = OSMMapsScanner(settings)
    leads = await scanner.scan("restaurant", "Austin TX", limit=5, no_website_only=False)
    print("scanner leads:", len(leads), [x.business_name for x in leads])


if __name__ == "__main__":
    asyncio.run(main())
