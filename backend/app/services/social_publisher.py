"""
SED Energy - Social Publisher Service
Publishes content to Facebook, Instagram, and LinkedIn via their respective APIs.
"""
import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger("sed-ai.social-publisher")


class SocialPublisherService:
    """
    Handles publishing to Facebook, Instagram (Meta Graph API), and LinkedIn.
    """

    def __init__(self):
        self.graph_base = f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}"
        self.li_base = "https://api.linkedin.com/v2"

    # ─── Facebook ────────────────────────────────────────────────────────────

    async def publish_facebook_post(
        self,
        message: str,
        image_url: Optional[str] = None,
        link: Optional[str] = None,
    ) -> dict:
        """Publish a text or image post to the Facebook Page"""
        async with httpx.AsyncClient() as client:
            if image_url:
                # Photo post
                payload = {
                    "message": message,
                    "url": image_url,
                    "access_token": settings.META_ACCESS_TOKEN,
                }
                endpoint = f"{self.graph_base}/{settings.META_PAGE_ID}/photos"
            else:
                # Text/link post
                payload = {
                    "message": message,
                    "access_token": settings.META_ACCESS_TOKEN,
                }
                if link:
                    payload["link"] = link
                endpoint = f"{self.graph_base}/{settings.META_PAGE_ID}/feed"

            response = await client.post(endpoint, data=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Facebook post published: {data.get('id')}")
            return {"platform": "facebook", "post_id": data.get("id"), "success": True}

    async def publish_facebook_carousel(self, message: str, image_urls: list) -> dict:
        """Publish a multi-image carousel to Facebook"""
        async with httpx.AsyncClient() as client:
            # Upload photos as unpublished attachments
            photo_ids = []
            for url in image_urls[:10]:
                r = await client.post(
                    f"{self.graph_base}/{settings.META_PAGE_ID}/photos",
                    data={"url": url, "published": False, "access_token": settings.META_ACCESS_TOKEN},
                    timeout=30.0,
                )
                r.raise_for_status()
                photo_ids.append({"media_fbid": r.json()["id"]})

            # Publish feed post with multiple attached media
            payload = {
                "message": message,
                "attached_media": str(photo_ids),
                "access_token": settings.META_ACCESS_TOKEN,
            }
            r = await client.post(
                f"{self.graph_base}/{settings.META_PAGE_ID}/feed",
                data=payload,
                timeout=30.0,
            )
            r.raise_for_status()
            return {"platform": "facebook", "post_id": r.json().get("id"), "success": True}

    # ─── Instagram ───────────────────────────────────────────────────────────

    async def publish_instagram_image(self, caption: str, image_url: str) -> dict:
        """Publish an image post to Instagram Business Account"""
        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            r = await client.post(
                f"{self.graph_base}/{settings.META_INSTAGRAM_ACCOUNT_ID}/media",
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": settings.META_ACCESS_TOKEN,
                },
                timeout=30.0,
            )
            r.raise_for_status()
            container_id = r.json()["id"]

            # Step 2: Publish container
            r2 = await client.post(
                f"{self.graph_base}/{settings.META_INSTAGRAM_ACCOUNT_ID}/media_publish",
                data={"creation_id": container_id, "access_token": settings.META_ACCESS_TOKEN},
                timeout=30.0,
            )
            r2.raise_for_status()
            post_id = r2.json().get("id")
            logger.info(f"Instagram post published: {post_id}")
            return {"platform": "instagram", "post_id": post_id, "success": True}

    async def publish_instagram_reel(self, caption: str, video_url: str) -> dict:
        """Publish a Reel to Instagram"""
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.graph_base}/{settings.META_INSTAGRAM_ACCOUNT_ID}/media",
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "share_to_feed": True,
                    "access_token": settings.META_ACCESS_TOKEN,
                },
                timeout=60.0,
            )
            r.raise_for_status()
            container_id = r.json()["id"]

            # Poll for processing completion
            import asyncio
            for _ in range(12):  # Try for ~60 seconds
                await asyncio.sleep(5)
                status_r = await client.get(
                    f"{self.graph_base}/{container_id}",
                    params={"fields": "status_code", "access_token": settings.META_ACCESS_TOKEN},
                )
                status = status_r.json().get("status_code")
                if status == "FINISHED":
                    break
                elif status == "ERROR":
                    raise Exception("Instagram video processing failed")

            r2 = await client.post(
                f"{self.graph_base}/{settings.META_INSTAGRAM_ACCOUNT_ID}/media_publish",
                data={"creation_id": container_id, "access_token": settings.META_ACCESS_TOKEN},
                timeout=30.0,
            )
            r2.raise_for_status()
            return {"platform": "instagram", "post_id": r2.json().get("id"), "success": True, "type": "reel"}

    # ─── LinkedIn ────────────────────────────────────────────────────────────

    async def publish_linkedin_post(
        self,
        text: str,
        image_url: Optional[str] = None,
    ) -> dict:
        """Publish a post to LinkedIn Company Page"""
        headers = {
            "Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        org_urn = f"urn:li:organization:{settings.LINKEDIN_ORGANIZATION_ID}"

        payload = {
            "author": org_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE" if not image_url else "IMAGE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        if image_url:
            asset_urn = await self._upload_linkedin_image(image_url)
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "description": {"text": "SED Energy"},
                "media": asset_urn,
            }]
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.li_base}/ugcPosts",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            r.raise_for_status()
            post_id = r.headers.get("X-RestLi-Id", r.json().get("id", ""))
            logger.info(f"LinkedIn post published: {post_id}")
            return {"platform": "linkedin", "post_id": post_id, "success": True}

    async def _upload_linkedin_image(self, image_url: str) -> str:
        """Upload an image to LinkedIn and return asset URN"""
        headers = {
            "Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        org_urn = f"urn:li:organization:{settings.LINKEDIN_ORGANIZATION_ID}"

        async with httpx.AsyncClient() as client:
            # Register upload
            r = await client.post(
                f"{self.li_base}/assets?action=registerUpload",
                headers=headers,
                json={
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "owner": org_urn,
                        "serviceRelationships": [{
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent",
                        }],
                    }
                },
                timeout=30.0,
            )
            r.raise_for_status()
            data = r.json()
            asset_urn = data["value"]["asset"]
            upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]

            # Download image and upload to LinkedIn
            img_r = await client.get(image_url, timeout=30.0)
            img_r.raise_for_status()
            await client.put(upload_url, content=img_r.content, timeout=60.0)

        return asset_urn

    async def publish(self, content_item: dict) -> dict:
        """Unified publish dispatcher"""
        platform = content_item.get("platform")
        body = content_item.get("body", "")
        caption = content_item.get("caption") or body
        image_url = content_item.get("image_url")
        video_url = content_item.get("video_url")
        content_type = content_item.get("content_type", "text_post")

        try:
            if platform == "facebook":
                if image_url:
                    return await self.publish_facebook_post(body, image_url=image_url)
                return await self.publish_facebook_post(body)
            elif platform == "instagram":
                if content_type in ["reel", "video"] and video_url:
                    return await self.publish_instagram_reel(caption, video_url)
                elif image_url:
                    return await self.publish_instagram_image(caption, image_url)
            elif platform == "linkedin":
                return await self.publish_linkedin_post(body, image_url=image_url)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
        except Exception as e:
            logger.error(f"Publish failed for {platform}: {e}", exc_info=True)
            return {"platform": platform, "success": False, "error": str(e)}
