"""
SED Energy - Image Generation Service
Generates branded images via Replicate (Flux SDXL), DALL-E 3, and Ideogram.
"""
import logging
import httpx
import asyncio
import boto3
from io import BytesIO
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger("sed-ai.image-gen")

REPLICATE_BASE = "https://api.replicate.com/v1"

# Flux SDXL model on Replicate
FLUX_MODEL = "black-forest-labs/flux-schnell"
FLUX_PRO_MODEL = "black-forest-labs/flux-1.1-pro"
SDXL_MODEL = "stability-ai/sdxl:39ed52f2319f9a1e13b23fdc5b82a9b75acee3a72fc29c7fcb9742bce27d8b26"


class ImageGenerationService:
    """
    Multi-provider image generation with S3 asset storage.
    Supports Flux (via Replicate), DALL-E 3 (OpenAI), and Ideogram.
    """

    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )

    async def generate_with_flux(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "1:1",
        quality: str = "standard",  # "standard" or "pro"
    ) -> Optional[str]:
        """Generate image using Flux via Replicate API"""
        if not settings.REPLICATE_API_TOKEN:
            logger.warning("Replicate API token not set")
            return None

        model = FLUX_PRO_MODEL if quality == "pro" else FLUX_MODEL

        async with httpx.AsyncClient() as client:
            # Create prediction
            r = await client.post(
                f"{REPLICATE_BASE}/models/{model}/predictions",
                headers={
                    "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio,
                        "output_format": "webp",
                        "output_quality": 90,
                        "safety_tolerance": 2,
                    }
                },
                timeout=30.0,
            )
            r.raise_for_status()
            prediction = r.json()
            prediction_id = prediction["id"]

            # Poll for completion
            for _ in range(60):
                await asyncio.sleep(2)
                poll_r = await client.get(
                    f"{REPLICATE_BASE}/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {settings.REPLICATE_API_TOKEN}"},
                    timeout=15.0,
                )
                poll_r.raise_for_status()
                result = poll_r.json()
                if result["status"] == "succeeded":
                    output_url = result["output"][0] if isinstance(result["output"], list) else result["output"]
                    return await self._download_and_store(output_url, f"flux_{prediction_id}.webp")
                elif result["status"] == "failed":
                    logger.error(f"Flux generation failed: {result.get('error')}")
                    return None

        return None

    async def generate_with_dalle3(
        self,
        prompt: str,
        size: str = "1024x1024",  # "1024x1024", "1792x1024", "1024x1792"
        quality: str = "standard",
    ) -> Optional[str]:
        """Generate image using DALL-E 3"""
        try:
            response = await self.openai.images.generate(
                model="dall-e-3",
                prompt=prompt[:4000],
                size=size,
                quality=quality,
                n=1,
            )
            image_url = response.data[0].url
            return await self._download_and_store(image_url, f"dalle_{size}.png")
        except Exception as e:
            logger.error(f"DALL-E 3 generation error: {e}")
            return None

    async def generate_with_ideogram(self, prompt: str, aspect_ratio: str = "ASPECT_1_1") -> Optional[str]:
        """Generate image using Ideogram API"""
        if not settings.IDEOGRAM_API_KEY:
            return None

        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(
                    "https://api.ideogram.ai/generate",
                    headers={"Api-Key": settings.IDEOGRAM_API_KEY},
                    json={
                        "image_request": {
                            "prompt": prompt,
                            "aspect_ratio": aspect_ratio,
                            "model": "V_2",
                            "magic_prompt_option": "AUTO",
                        }
                    },
                    timeout=60.0,
                )
                r.raise_for_status()
                data = r.json()
                url = data["data"][0]["url"]
                return await self._download_and_store(url, "ideogram.png")
            except Exception as e:
                logger.error(f"Ideogram error: {e}")
                return None

    async def generate(
        self,
        prompt: str,
        platform: str,
        content_type: str,
        provider: str = "flux",
    ) -> Optional[str]:
        """Unified image generation dispatcher with platform-aware sizing"""
        # Map platform/content_type to dimensions
        size_map = {
            ("instagram", "feed"): ("1:1", "1024x1024"),
            ("instagram", "story"): ("9:16", "1024x1792"),
            ("instagram", "reel"): ("9:16", "1024x1792"),
            ("facebook", "post"): ("1.91:1", "1792x1024"),
            ("linkedin", "post"): ("1.91:1", "1792x1024"),
        }
        aspect_ratio, dalle_size = size_map.get((platform, content_type), ("1:1", "1024x1024"))

        # Try providers in priority order
        if provider == "flux" and settings.REPLICATE_API_TOKEN:
            url = await self.generate_with_flux(prompt, aspect_ratio=aspect_ratio)
            if url:
                return url

        if settings.OPENAI_API_KEY:
            url = await self.generate_with_dalle3(prompt, size=dalle_size)
            if url:
                return url

        if settings.IDEOGRAM_API_KEY:
            return await self.generate_with_ideogram(prompt)

        logger.error("All image generation providers failed or not configured")
        return None

    async def _download_and_store(self, url: str, filename: str) -> str:
        """Download image and store in S3, return permanent URL"""
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=60.0)
            r.raise_for_status()
            image_bytes = r.content

        s3_key = f"generated-images/{filename}"
        self.s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/webp" if filename.endswith(".webp") else "image/png",
            ACL="public-read",
        )

        # Return public URL
        if settings.S3_ENDPOINT_URL:
            return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{s3_key}"
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
