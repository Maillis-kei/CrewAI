import argparse
import json
import os
import subprocess
import time
from video_generator import VideoGenerator

def get_ffmpeg_binary():
    """시스템 ffmpeg 또는 imageio_ffmpeg 바이너리 경로 탐색"""
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True)
        if res.returncode == 0:
            return "ffmpeg"
    except Exception:
        pass
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return "ffmpeg"

def merge_videos(video_files: list[str], output_path: str) -> bool:
    """개별 씬 비디오들을 하나의 완성본 MP4로 자동 무손실 병합"""
    if not video_files:
        return False
    if len(video_files) == 1:
        import shutil
        shutil.copyfile(video_files[0], output_path)
        return True

    ffmpeg_bin = get_ffmpeg_binary()
    temp_list_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")

    try:
        with open(temp_list_file, "w", encoding="utf-8") as f:
            for vf in video_files:
                abs_p = os.path.abspath(vf).replace("\\", "/")
                f.write(f"file '{abs_p}'\n")

        print(f"\n🎬 [자동 병합] {len(video_files)}개 씬을 하나의 최종 영상으로 병합 중...")
        cmd = [
            ffmpeg_bin, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list_file,
            "-c", "copy",
            output_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[✓] 최종 합본 영상 생성 완료: {output_path}")
            if os.path.exists(temp_list_file):
                os.remove(temp_list_file)
            return True
        else:
            print(f"[!] 영상 병합 실패: {res.stderr}")
            return False
    except Exception as e:
        print(f"[!] 병합 중 오류 발생: {e}")
        return False

def run_batch(scenes_file: str = "scenes.json", output_dir: str = "/content/drive/MyDrive/ai_videos"):
    """scenes.json을 파싱하여 모든 씬을 연속 렌더링"""
    if not os.path.exists(scenes_file):
        print(f"[!] 오류: '{scenes_file}' 파일을 찾을 수 없습니다.")
        print("💡 안내: CrewAI로 scenes.json을 먼저 생성하거나 git pull로 동기화하세요.")
        return

    with open(scenes_file, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    if not isinstance(scenes, list):
        print(f"[!] scenes.json 형식이 올바르지 않습니다. 리스트 형태여야 합니다.")
        return

    print("="*60)
    print(f"🚀 배치 비디오 생성 파이프라인 시작 (총 {len(scenes)}개 씬)")
    print(f"📁 출력 대상 디렉토리: {output_dir}")
    print("="*60)

    os.makedirs(output_dir, exist_ok=True)

    # 1. 모델 파이프라인 1회 로드 (중복 로딩 방지 및 VRAM 절약)
    print("\n[*] AnimateDiff 파이프라인 초기화 중...")
    generator = VideoGenerator()

    # 2. 각 씬 순차 생성
    start_total_time = time.time()
    generated_files = []

    for index, scene in enumerate(scenes, start=1):
        scene_id = scene.get("scene_id", index)
        file_name = scene.get("file_name", f"scene_{scene_id:02d}.mp4")
        prompt = scene.get("prompt", "")
        negative_prompt = scene.get("negative_prompt", "bad quality, blurry, distorted, deformed")
        num_frames = scene.get("num_frames", 16)
        guidance_scale = scene.get("guidance_scale", 7.5)
        num_inference_steps = scene.get("num_inference_steps", 25)

        target_path = os.path.join(output_dir, file_name)

        print(f"\n[{index}/{len(scenes)}] 씬 {scene_id} 렌더링 진행 중...")
        print(f"  - 파일: {file_name}")
        print(f"  - 프롬프트: {prompt}")

        scene_start = time.time()
        output_path = generator.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            output_path=target_path,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale
        )
        elapsed = time.time() - scene_start
        print(f"  ✓ 씬 {scene_id} 완료 ({elapsed:.1f}초 소요)")
        generated_files.append(output_path)

    total_elapsed = time.time() - start_total_time
    print("\n" + "="*60)
    print(f"🎉 모든 씬 렌더링이 성공적으로 완료되었습니다!")
    print(f"⏱ 총 소요 시간: {total_elapsed:.1f}초")
    print("📦 생성된 개별 비디오 목록:")
    for f in generated_files:
        print(f"  - {f}")
    
    # 3. 모든 씬을 하나의 완성본 비디오로 자동 병합
    combined_movie_path = os.path.join(output_dir, "final_combined_movie.mp4")
    merge_videos(generated_files, combined_movie_path)
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Colab 배치 비디오 생성기")
    parser.add_argument("--scenes_file", type=str, default="scenes.json", help="씬 정의 JSON 파일 경로")
    parser.add_argument("--output_dir", type=str, default="/content/drive/MyDrive/ai_videos", help="Google Drive 또는 로컬 저장 경로")
    args = parser.parse_args()

    run_batch(scenes_file=args.scenes_file, output_dir=args.output_dir)
