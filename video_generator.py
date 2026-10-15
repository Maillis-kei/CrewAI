import os
import sys
import subprocess
import requests
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

def get_ffmpeg_cmd():
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

def ensure_korean_font():
    local_font = "NanumGothicBold.ttf"
    if os.path.exists(local_font):
        return local_font
    
    system_fonts = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for p in system_fonts:
        if os.path.exists(p):
            return p
            
    print("시스템 한글 폰트를 찾지 못하여 나눔고딕 폰트를 다운로드합니다...")
    try:
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(local_font, "wb") as f:
                f.write(r.content)
            return local_font
    except Exception as e:
        print(f"폰트 다운로드 실패: {e}")
        
    return None

def get_font(size=40, bold=False):
    font_path = ensure_korean_font()
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def get_audio_duration(audio_path, ffmpeg_bin):
    cmd = [ffmpeg_bin, "-i", audio_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 5.0

def create_scene_image(scene, output_image_path):
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(15, 23, 42))  # Dark Slate
    draw = ImageDraw.Draw(img)

    accent_rgb = hex_to_rgb(scene.get("accent", "#38bdf8"))

    # Top Header
    font_header = get_font(32, bold=True)
    draw.rectangle([0, 0, width, 140], fill=(10, 15, 30))
    draw.text((width // 2, 70), "📱 iPad Coding Hacks | YouTube Shorts", fill=(148, 163, 184), font=font_header, anchor="mm")

    # Step Badge
    badge_text = f"  {scene.get('badge', 'POINT')}  "
    font_badge = get_font(38, bold=True)
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox_b[2] - bbox_b[0], bbox_b[3] - bbox_b[1]
    bx = (width - bw) // 2
    by = 260
    draw.rounded_rectangle([bx - 20, by - 12, bx + bw + 20, by + bh + 12], radius=25, fill=accent_rgb)
    draw.text((width // 2, by + bh // 2), badge_text.strip(), fill=(0, 0, 0), font=font_badge, anchor="mm")

    # Main Title
    font_title = get_font(60, bold=True)
    title_lines = wrap_text(scene.get("title", ""), font_title, 940, draw)
    ty = 420
    for tl in title_lines:
        draw.text((width // 2, ty), tl, fill=(255, 255, 255), font=font_title, anchor="mm")
        ty += 80

    # Center Feature Card
    card_top = max(ty + 60, 680)
    card_bottom = card_top + 460
    draw.rounded_rectangle([80, card_top, width - 80, card_bottom], radius=30, fill=(30, 41, 59), outline=accent_rgb, width=4)

    # Card Content
    font_highlight = get_font(46, bold=True)
    hl_lines = wrap_text(scene.get("highlight", ""), font_highlight, 840, draw)
    cy = card_top + 180
    for hl in hl_lines:
        draw.text((width // 2, cy), hl, fill=(241, 245, 249), font=font_highlight, anchor="mm")
        cy += 70

    # Bottom Subtitle Box
    sub_box_top = 1380
    sub_box_bottom = 1760
    draw.rounded_rectangle([60, sub_box_top, width - 60, sub_box_bottom], radius=25, fill=(0, 0, 0))
    draw.rounded_rectangle([60, sub_box_top, width - 60, sub_box_bottom], radius=25, outline=(71, 85, 105), width=2)

    font_sub = get_font(42, bold=True)
    sub_lines = wrap_text(scene.get("narration", ""), font_sub, 880, draw)
    sy = sub_box_top + 70
    for sl in sub_lines[:4]:
        draw.text((width // 2, sy), sl, fill=(255, 230, 0), font=font_sub, anchor="mm")  # Highlight Yellow
        sy += 65

    img.save(output_image_path)

def generate_shorts_video(scenes, output_mp4="shorts_video.mp4"):
    ffmpeg_bin = get_ffmpeg_cmd()
    print(f"Using FFmpeg: {ffmpeg_bin}")

    os.makedirs("temp_shorts", exist_ok=True)
    clip_files = []

    print(f"총 {len(scenes)}개의 씬 렌더링을 시작합니다...")

    for i, sc in enumerate(scenes):
        badge = sc.get('badge', f'Scene {i+1}')
        print(f"\n[Scene {i+1}/{len(scenes)}] {badge} 처리 중...")
        
        # 1. Voice generation
        audio_path = f"temp_shorts/scene_{i}.mp3"
        tts = gTTS(text=sc.get("narration", ""), lang="ko")
        tts.save(audio_path)
        duration = get_audio_duration(audio_path, ffmpeg_bin) + 0.3
        print(f"  - 오디오 생성 완료 (길이: {duration:.2f}초)")

        # 2. Visual card generation
        image_path = f"temp_shorts/scene_{i}.png"
        create_scene_image(sc, image_path)
        print("  - 비주얼 그래픽 카드 생성 완료")

        # 3. Render clip
        clip_path = f"temp_shorts/clip_{i}.mp4"
        cmd = [
            ffmpeg_bin, "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            clip_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"클립 렌더링 에러: {res.stderr}")
            raise RuntimeError("Clip rendering failed")
        
        clip_files.append(clip_path)

    # 4. Concatenate all clips
    concat_list_path = "temp_shorts/concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for cf in clip_files:
            abs_path = os.path.abspath(cf).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    print("\n모든 씬을 하나의 쇼츠 비디오로 병합합니다...")
    concat_cmd = [
        ffmpeg_bin, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_mp4
    ]
    res = subprocess.run(concat_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("병합 에러:", res.stderr)
        raise RuntimeError("Concat failed")

    size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"비디오 렌더링 성공: {output_mp4} ({size_mb:.2f} MB)")
    return output_mp4
