"""
SED Energy - Video Agent
Generates video prompts + handles Runway/Pika/Kling API calls for AI video generation.
Manages FFmpeg post-processing: subtitles, brand overlays, music.
"""
import logging
import json
import httpx
from typing import Optional
from anthropic import AsyncAnthropic
from app.config import settings
from app.core.prompts import SED_MASTER_SYSTEM_PROMPT

logger = logging.getLogger("sed-ai.video-agent")

VIDEO_FORMATS = {
    "instagram_reel": {"duration": 30, "aspect": "9:16", "resolution": "1080x1920"},
    "instagram_story": {"duration": 15, "aspect": "9:16", "resolution": "1080x1920"},
    "tiktok": {"duration": 30, "aspect": "9:16", "resolution": "1080x1920"},
    "facebook_reel": {"duration": 60, "aspect": "9:16", "resolution": "1080x1920"},
    "linkedin_video": {"duration": 60, "aspect": "16:9", "resolution": "1920x1080"},
    "youtube_short": {"duration": 60, "aspect": "9:16", "resolution": "1080x1920"},
}

VIDEO_STYLE_TEMPLATES = {
    "stock_arrival": {
        "style": "cinematic warehouse walkthrough, pan across solar equipment, dramatic lighting",
        "mood": "energetic, professional, exciting",
        "music_style": "upbeat corporate, modern tech",
        "voiceover": True,
    },
    "educational": {
        "style": "clean motion graphics, data visualization, talking-head explainer style",
        "mood": "informative, trustworthy, calm",
        "music_style": "subtle ambient, educational",
        "voiceover": True,
    },
    "product_showcase": {
        "style": "360 product rotation, close-up detail shots, hero lighting",
        "mood": "premium, technical, impressive",
        "music_style": "minimal modern tech",
        "voiceover": False,
    },
    "installer_content": {
        "style": "on-site installation footage, South African rooftop, timelapse option",
        "mood": "authentic, skilled, trustworthy",
        "music_style": "energetic but professional",
        "voiceover": False,
    },
}

BRAND_OVERLAY_CONFIG = {
    "logo_position": "bottom_right",
    "logo_opacity": 0.9,
    "lower_third_color": "#E85A0C",
    "font": "Inter Bold",
    "subtitle_style": "white on dark background, bottom 15%",
    "watermark": "sed.energy",
    "end_card_duration": 3,
}


class VideoAgent:
    """
    Generates AI video prompts and manages video generation pipeline.
    Supports Runway ML, Pika, and Kling APIs.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, state: dict) -> dict:
        platform = state.get("platform", "instagram")
        content_type = state.get("content_type", "reel")
        topic = state.get("topic", "")
        generated_content = state.get("generated_content", {})

        # Determine video format
        format_key = f"{platform}_{content_type}" if f"{platform}_{content_type}" in VIDEO_FORMATS else "instagram_reel"
        video_format = VIDEO_FORMATS.get(format_key, VIDEO_FORMATS["instagram_reel"])

        # Determine style template
        style_key = topic if topic in VIDEO_STYLE_TEMPLATES else "product_showcase"
        style_template = VIDEO_STYLE_TEMPLATES.get(style_key, VIDEO_STYLE_TEMPLATES["product_showcase"])

        # Generate video prompt
        video_prompt = await self._generate_video_prompt(
            topic=topic,
            content=generated_content,
            platform=platform,
            video_format=video_format,
            style_template=style_template,
        )

        # Generate voiceover script if needed
        voiceover_script = None
        if style_template.get("voiceover"):
            voiceover_script = await self._generate_voiceover_script(
                content=generated_content,
                duration=video_format["duration"],
                platform=platform,
            )

        return {
            "video_prompt": video_prompt,
            "video_data": {
                "prompt": video_prompt,
                "format": video_format,
                "style": style_template,
                "voiceover_script": voiceover_script,
                "brand_overlay": BRAND_OVERLAY_CONFIG,
                "platform": platform,
                "ffmpeg_instructions": self._get_ffmpeg_instructions(video_format),
            },
        }

    async def _generate_video_prompt(
        self, topic: str, content: dict, platform: str,
        video_format: dict, style_template: dict
    ) -> str:
        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}

Generate a video generation prompt for Runway ML or Kling AI.
The video is for SED Energy, South Africa's Tier 1 solar distributor.

Rules:
- Be specific about camera movements (pan, zoom, dolly, aerial)
- Describe lighting (golden hour, studio, cinematic)
- Include South African context where relevant
- Keep to {video_format['duration']} seconds max
- Aspect ratio: {video_format['aspect']}
- Style: {style_template['style']}
- Mood: {style_template['mood']}
- NO text visible in the video (text added in post-production)

Return ONLY the video generation prompt text, no JSON.
"""
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Topic: {topic}\nContent brief: {content.get('body', '')}\nPlatform: {platform}"
            }],
        )
        return response.content[0].text.strip()

    async def _generate_voiceover_script(self, content: dict, duration: int, platform: str) -> str:
        """Generate a voiceover script timed to video duration (approx 2.5 words/second)"""
        word_count = int(duration * 2.5)
        system_prompt = f"""{SED_MASTER_SYSTEM_PROMPT}
Write a professional voiceover script for a {duration}-second video.
Target: ~{word_count} words. Tone: authoritative, trusted solar expert.
No filler words. Strong opening hook. Clear closing CTA.
Return ONLY the script text.
"""
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Content: {content.get('body', '')}"}],
        )
        return response.content[0].text.strip()

    def _get_ffmpeg_instructions(self, video_format: dict) -> dict:
        """Returns FFmpeg post-processing instructions for brand overlays"""
        return {
            "resize": f"-vf scale={video_format['resolution'].replace('x', ':')}",
            "subtitle_filter": "subtitles=output.srt:force_style='FontName=Inter,FontSize=14,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'",
            "logo_overlay": "overlay=W-w-20:H-h-20",
            "lower_third": f"drawbox=0:H-60:iw:60:color=#E85A0C@0.9:t=fill",
            "output_format": "-c:v libx264 -crf 18 -preset slow -c:a aac -b:a 192k",
            "instagram_reel_export": "-vf 'scale=1080:1920,setsar=1' -t 30",
        }

    async def trigger_runway_generation(self, prompt: str, image_url: Optional[str] = None) -> dict:
        """Call Runway ML API for video generation"""
        if not settings.RUNWAY_API_KEY:
            logger.warning("Runway API key not configured")
            return {"status": "skipped", "reason": "No Runway API key"}

        async with httpx.AsyncClient() as client:
            payload = {
                "promptText": prompt,
                "model": "gen3a_turbo",
                "duration": 10,
                "ratio": "9:16",
            }
            if image_url:
                payload["promptImage"] = image_url

            response = await client.post(
                "https://api.dev.runwayml.com/v1/image_to_video",
                headers={
                    "Authorization": f"Bearer {settings.RUNWAY_API_KEY}",
                    "X-Runway-Version": "2024-11-06",
                },
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
