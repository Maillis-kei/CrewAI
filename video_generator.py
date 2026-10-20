import argparse
import datetime
import os
import torch
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
from diffusers.utils import export_to_video

class VideoGenerator:
    """AnimateDiff 모델을 메모리에 상주시켜 다수의 씬을 고속 생성하는 배치 최적화 클래스"""

    def __init__(
        self,
        motion_adapter_id: str = "guoyww/animatediff-motion-adapter-v1-5-2",
        base_model_id: str = "SG161222/Realistic_Vision_V5.1_noVAE",
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[*] 실행 디바이스: {self.device}")
        if self.device != "cuda":
            print("[!] 경고: GPU(CUDA)가 감지되지 않았습니다. T4 GPU 이상 환경을 권장합니다.")

        print(f"[*] AnimateDiff 모션 어댑터 로드 중: {motion_adapter_id}...")
        self.adapter = MotionAdapter.from_pretrained(
            motion_adapter_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )

        print(f"[*] 확산 모델 파이프라인 로드 중: {base_model_id}...")
        self.pipeline = AnimateDiffPipeline.from_pretrained(
            base_model_id,
            motion_adapter=self.adapter,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )

        # DDIM 스케줄러 설정
        scheduler = DDIMScheduler.from_pretrained(
            base_model_id,
            subfolder="scheduler",
            clip_sample=False,
            timestep_spacing="linspace",
            steps_offset=1
        )
        self.pipeline.scheduler = scheduler

        # VRAM 최적화 (Colab T4 16GB 메모리 초과 방지)
        if self.device == "cuda":
            print("[*] VRAM 최적화 적용 (CPU Offload)...")
            self.pipeline.enable_model_cpu_offload()
            if hasattr(self.pipeline, "enable_vae_slicing"):
                self.pipeline.enable_vae_slicing()
            elif hasattr(self.pipeline, "vae") and hasattr(self.pipeline.vae, "enable_slicing"):
                self.pipeline.vae.enable_slicing()

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "bad quality, blurry, distorted, deformed, low resolution",
        output_path: str = "output.mp4",
        num_frames: int = 16,
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        fps: int = 8,
        seed: int = 42
    ) -> str:
        """단일 씬 비디오 생성"""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        print(f"\n🎬 비디오 생성 시작: '{prompt[:60]}...'")
        print(f"   - 프레임 수: {num_frames}, 스텝 수: {num_inference_steps}, 출력 파일: {output_path}")

        generator = torch.Generator(self.device).manual_seed(seed) if self.device == "cuda" else torch.Generator("cpu").manual_seed(seed)

        output = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            width=width,
            height=height,
            generator=generator,
        )
        frames = output.frames[0]

        export_to_video(frames, output_path, fps=fps)
        print(f"[✓] 생성 완료: {output_path}")
        return output_path


def generate_video(
    prompt: str,
    negative_prompt: str = "bad quality, blurry, distorted, deformed, low resolution",
    output_dir: str = "/content/drive/MyDrive/ai_videos",
    file_name: str = None,
    num_frames: int = 16,
    num_inference_steps: int = 25,
    guidance_scale: float = 7.5,
    width: int = 512,
    height: int = 512,
) -> str:
    """단일 실행용 편의 함수 (기존 스크립트 호환)"""
    os.makedirs(output_dir, exist_ok=True)
    if not file_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"video_{timestamp}.mp4"
    output_path = os.path.join(output_dir, file_name)

    generator = VideoGenerator()
    return generator.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        output_path=output_path,
        num_frames=num_frames,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        width=width,
        height=height
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AnimateDiff Video Generator")
    parser.add_argument("--prompt", type=str, default="a cinematic shot of an astronaut riding a horse on Mars, photorealistic, 4k")
    parser.add_argument("--negative_prompt", type=str, default="bad quality, blurry, distorted, deformed, low resolution")
    parser.add_argument("--output_dir", type=str, default="./outputs")
    parser.add_argument("--file_name", type=str, default="test_scene.mp4")
    parser.add_argument("--num_frames", type=int, default=16)
    parser.add_argument("--steps", type=int, default=25)

    args = parser.parse_args()
    generate_video(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        output_dir=args.output_dir,
        file_name=args.file_name,
        num_frames=args.num_frames,
        num_inference_steps=args.steps
    )
