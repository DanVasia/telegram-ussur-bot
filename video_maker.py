import os
import subprocess
import tempfile

def make_short_video(text, media_path=None, output_path="shorts_video.mp4"):
    """
    Создаёт вертикальное видео 9:16 длительностью ~10 секунд.
    - Если есть media_path (фото или видео) – использует его как фон.
    - Если нет – создаёт чёрный фон с текстом.
    Возвращает путь к созданному видео.
    """
    # Если есть медиа-файл
    if media_path and os.path.exists(media_path):
        # Определяем тип файла (фото или видео) по расширению
        ext = os.path.splitext(media_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            # Это фото: создаём видео из фото с наложением текста
            cmd = [
                "ffmpeg", "-loop", "1", "-i", media_path,
                "-vf", f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,drawtext=text='{text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=h-text_h-50:box=1:boxcolor=black@0.5:boxborderw=10",
                "-c:a", "aac", "-b:a", "128k", "-t", "10",
                output_path
            ]
        else:
            # Это видео: обрезаем до вертикали и накладываем текст
            cmd = [
                "ffmpeg", "-i", media_path,
                "-vf", f"crop=iw:ih*9/16,scale=1080:1920,drawtext=text='{text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=h-text_h-50:box=1:boxcolor=black@0.5:boxborderw=10",
                "-c:a", "aac", "-b:a", "128k", "-t", "10",
                output_path
            ]
    else:
        # Нет медиа – чёрный фон с текстом
        cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=10",
            "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5:boxborderw=20",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
