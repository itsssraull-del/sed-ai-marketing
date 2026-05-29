"""Media generation routes — images, videos, design prompts"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.models.user import User
from app.core.security import get_current_user, require_editor
from app.services.image_generation import ImageGenerationService
from app.agents.design_agent import DesignAgent
from app.agents.video_agent import VideoAgent

router = APIRouter()


class GenerateImageRequest(BaseModel):
    prompt: str
    platform: str = "instagram"
    content_type: str = "feed"
    provider: str = "flux"  # flux | dalle3 | ideogram
    auto_design_prompt: bool = False
    topic: Optional[str] = None


class GenerateVideoRequest(BaseModel):
    topic: str
    platform: str = "instagram"
    content_type: str = "reel"
    content_body: Optional[str] = None
    image_url: Optional[str] = None


class GenerateDesignPromptRequest(BaseModel):
    topic: str
    platform: str
    content_type: str
    content_body: Optional[str] = None
    image_description: Optional[str] = None


@router.post("/generate-image")
async def generate_image(
    request: GenerateImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_editor),
):
    """Generate a branded image using AI"""
    prompt = request.prompt

    # Optionally enhance prompt via Design Agent
    if request.auto_design_prompt and request.topic:
        design_agent = DesignAgent()
        design_state = {
            "platform": request.platform,
            "content_type": request.content_type,
            "topic": request.topic,
            "generated_content": {"image_description": request.prompt},
        }
        design_result = await design_agent.run(design_state)
        prompt = design_result.get("design_prompt", request.prompt)

    service = ImageGenerationService()
    image_url = await service.generate(
        prompt=prompt,
        platform=request.platform,
        content_type=request.content_type,
        provider=request.provider,
    )

    if not image_url:
        raise HTTPException(status_code=500, detail="Image generation failed. Check API keys and provider status.")

    return {
        "image_url": image_url,
        "prompt_used": prompt,
        "platform": request.platform,
        "provider": request.provider,
    }


@router.post("/generate-design-prompt")
async def generate_design_prompt(
    request: GenerateDesignPromptRequest,
    current_user: User = Depends(require_editor),
):
    """Generate an optimised image generation prompt via the Design Agent"""
    agent = DesignAgent()
    state = {
        "platform": request.platform,
        "content_type": request.content_type,
        "topic": request.topic,
        "generated_content": {
            "body": request.content_body or "",
            "image_description": request.image_description or request.topic,
        },
    }
    result = await agent.run(state)
    return {
        "prompt": result.get("design_prompt"),
        "design_data": result.get("design_data"),
    }


@router.post("/generate-video-prompt")
async def generate_video_prompt(
    request: GenerateVideoRequest,
    current_user: User = Depends(require_editor),
):
    """Generate a video prompt + voiceover script via the Video Agent"""
    agent = VideoAgent()
    state = {
        "platform": request.platform,
        "content_type": request.content_type,
        "topic": request.topic,
        "generated_content": {"body": request.content_body or ""},
    }
    result = await agent.run(state)
    return {
        "video_prompt": result.get("video_prompt"),
        "video_data": result.get("video_data"),
    }


@router.post("/generate-video")
async def trigger_video_generation(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_editor),
):
    """Trigger Runway ML video generation"""
    agent = VideoAgent()
    state = {
        "platform": request.platform,
        "content_type": request.content_type,
        "topic": request.topic,
        "generated_content": {"body": request.content_body or ""},
    }
    video_result = await agent.run(state)
    prompt = video_result.get("video_prompt", "")

    if not prompt:
        raise HTTPException(status_code=400, detail="Could not generate video prompt")

    # Trigger async generation
    runway_result = await agent.trigger_runway_generation(prompt, image_url=request.image_url)

    return {
        "status": "triggered",
        "prompt": prompt,
        "runway_response": runway_result,
    }
