"""
Fetch leads for Category A Methods 01–17 (AGENT_EARNING_METHODS.md).
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config import Settings
from core.lead_sources import normalize_mode
from modules.lead_finder.scanners.google_maps import MapsScanResult


async def fetch_leads(
    settings: Settings,
    llm: Any,
    *,
    niche: str,
    city: str,
    limit: int,
    hunt_mode: str,
    scan_local_fn: Any,
) -> tuple[list[MapsScanResult], str]:
    mode = normalize_mode(hunt_mode)

    try:
        if mode == "m10_no_website":
            leads, src = await scan_local_fn(niche, city, limit, no_website_only=True)
            return leads, src or "m10"

        if mode == "m02_outdated":
            raw, base = await scan_local_fn(niche, city, max(limit * 4, 20), no_website_only=False)
            from modules.lead_finder.scanners.outdated_site import OutdatedSiteScanner

            filtered = await OutdatedSiteScanner(settings, llm).filter_outdated_maps_leads(
                raw,
                limit=limit,
                sparse_fallback=getattr(settings, "m02_sparse_fallback", True),
            )
            return filtered, f"{base}_m02"

        if mode == "m04_low_reviews":
            from modules.lead_finder.scanners.google_reviews import GoogleReviewsMonitor

            mon = GoogleReviewsMonitor(settings)
            return [mon.to_maps_result(r) for r in await mon.scan(niche, city, limit=limit)], "m04"

        if mode == "m17_apollo":
            from modules.lead_finder.scanners.apollo_leads import ApolloLeadScanner

            return await ApolloLeadScanner(settings).scan(niche, city, limit=limit), "m17"

        if mode == "m01_broken_link":
            from modules.lead_finder.scanners.broken_link import BrokenLinkScanner

            return (
                await BrokenLinkScanner(settings).scan_maps(niche, city, limit, scan_local_fn),
                "m01",
            )

        if mode == "m03_reddit":
            from modules.lead_finder.scanners.reddit_miner import RedditMiner

            return await RedditMiner(settings, llm).scan_maps(niche, city, limit), "m03"

        if mode == "m05_job_board":
            from modules.lead_finder.scanners.job_board import JobBoardScraper

            return await JobBoardScraper(settings, llm).scan_maps(city, limit=limit), "m05"

        if mode == "m11_linkedin_jobs":
            from modules.lead_finder.scanners.job_board import LinkedInJobMonitor

            return await LinkedInJobMonitor(settings, llm).scan_maps(city, limit=limit), "m11"

        if mode == "m06_youtube":
            from modules.lead_finder.scanners.youtube_auditor import YouTubeAuditor

            return await YouTubeAuditor(settings, llm).scan_maps(niche, city, limit), "m06"

        if mode == "m07_app_review":
            from modules.lead_finder.scanners.app_review import AppReviewMiner

            return await AppReviewMiner(settings, llm).scan_maps(niche, limit=limit), "m07"

        if mode == "m08_etsy_amazon":
            from modules.lead_finder.scanners.etsy_amazon import EtsyAmazonOptimizer

            return await EtsyAmazonOptimizer(settings, llm).scan_maps(niche, limit=limit), "m08"

        if mode == "m09_social_dm":
            from modules.lead_finder.scanners.social_dm import SocialDMScanner

            return await SocialDMScanner(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m09"

        if mode == "m12_producthunt":
            from modules.lead_finder.scanners.producthunt import ProductHuntMonitor

            return await ProductHuntMonitor(settings, llm).scan_maps(limit=limit), "m12"

        if mode == "m13_forum":
            from modules.lead_finder.scanners.forum_answers import ForumAnswerMarketer

            return await ForumAnswerMarketer(settings, llm).scan_maps(niche, limit=limit), "m13"

        if mode == "m14_saas_churn":
            from modules.lead_finder.scanners.saas_churn import SaaSChurnScanner

            return await SaaSChurnScanner(settings, llm).scan_maps(niche, limit=limit), "m14"

        if mode == "m15_shopify":
            from modules.lead_finder.scanners.shopify_auditor import ShopifyAuditor

            return await ShopifyAuditor(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m15"

        if mode == "m16_podcast":
            from modules.lead_finder.scanners.podcast_outreach import PodcastOutreacher

            return await PodcastOutreacher(settings, llm).scan_maps(niche, limit=limit), "m16"

        if mode == "m24_chatbot":
            from modules.lead_finder.scanners.website_automation import NoAutomationScanner

            return await NoAutomationScanner(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m24"

        if mode == "m25_social_only":
            from modules.lead_finder.scanners.website_automation import SocialOnlyScanner

            return await SocialOnlyScanner(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m25"

        if mode == "m26_new_business":
            from modules.lead_finder.scanners.website_automation import NewBusinessScanner

            return await NewBusinessScanner(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m26"

        if mode == "m27_no_booking":
            from modules.lead_finder.scanners.website_automation import NoBookingScanner

            return await NoBookingScanner(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m27"

        if mode == "m28_no_ordering":
            from modules.lead_finder.scanners.website_automation import NoOrderingScanner

            return await NoOrderingScanner(settings, llm).scan_maps(
                niche, city, limit, scan_local_fn
            ), "m28"

        logger.warning(f"[LeadFetcher] unknown mode {mode}, fallback m10")
        leads, src = await scan_local_fn(niche, city, limit, no_website_only=True)
        return leads, src

    except Exception as e:
        logger.error(f"[LeadFetcher] {mode} failed: {e}")
        return [], f"{mode}_error"
