from typing import List, Optional
from pydantic import BaseModel, Field

class SceneItem(BaseModel):
    scene_id: int = Field(..., description="씬 순서 번호 (1부터 시작)")
    file_name: str = Field(..., description="저장될 비디오 파일명 (예: scene_01.mp4)")
    prompt: str = Field(..., description="AnimateDiff용 영문 포지티브 프롬프트")
    negative_prompt: str = Field(
        default="blurry, deformed, flickering, low quality, bad anatomy, text, watermark",
        description="영문 네거티브 프롬프트"
    )
    num_frames: int = Field(default=16, description="생성할 프레임 수 (기본: 16)")
    guidance_scale: float = Field(default=7.5, description="CFG 스케일 (기본: 7.5)")
    num_inference_steps: int = Field(default=25, description="추론 스텝 수 (기본: 25)")

class SceneList(BaseModel):
    scenes: List[SceneItem] = Field(..., description="생성할 씬 목록")
