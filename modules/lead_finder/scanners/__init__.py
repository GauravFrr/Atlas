"""
Lead Finder Scanners — package init.
Each scanner is a self-contained module with a `scan()` async function
that returns a list of Lead-compatible dicts for the outreach pipeline.
"""
from .broken_link import BrokenLinkScanner
from .outdated_site import OutdatedSiteScanner
from .reddit_miner import RedditMiner
from .google_reviews import GoogleReviewsMonitor
from .job_board import JobBoardScraper
from .youtube_auditor import YouTubeAuditor
from .app_review import AppReviewMiner
from .etsy_amazon import EtsyAmazonOptimizer
from .social_dm import SocialDMScanner
from .google_maps import GoogleMapsScanner
from .osm_maps import OSMMapsScanner
from .producthunt import ProductHuntMonitor
from .forum_answers import ForumAnswerMarketer
from .saas_churn import SaaSChurnScanner
from .shopify_auditor import ShopifyAuditor
from .podcast_outreach import PodcastOutreacher
from .cold_email_core import ColdEmailCore

__all__ = [
    "BrokenLinkScanner",
    "OutdatedSiteScanner",
    "RedditMiner",
    "GoogleReviewsMonitor",
    "JobBoardScraper",
    "YouTubeAuditor",
    "AppReviewMiner",
    "EtsyAmazonOptimizer",
    "SocialDMScanner",
    "GoogleMapsScanner",
    "OSMMapsScanner",
    "ProductHuntMonitor",
    "ForumAnswerMarketer",
    "SaaSChurnScanner",
    "ShopifyAuditor",
    "PodcastOutreacher",
    "ColdEmailCore",
]
