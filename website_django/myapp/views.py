import json
import shutil
import yt_dlp
import whisper
from moviepy.editor import VideoFileClip
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
import os
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect  # 安装 langdetect 库用于语言检测

# 初始化 Whisper 模型
whisper_model = whisper.load_model("base")

# 语言模型字典
translation_models = {
    "en-ja": "Helsinki-NLP/opus-tatoeba-en-ja",
    "pt-en": "Helsinki-NLP/opus-mt-mul-en",
    "zh-en": "Helsinki-NLP/opus-mt-zh-en",
    "en-zh": "Helsinki-NLP/opus-mt-en-zh",
    "ja-en": "Helsinki-NLP/opus-mt-ja-en",
    "ko-en": "Helsinki-NLP/opus-mt-ko-en",
    "en-ko": "Helsinki-NLP/opus-mt-en-ko",
    "ar-en": "Helsinki-NLP/opus-mt-ar-en",
    "en-ar": "Helsinki-NLP/opus-mt-en-ar",
    "ru-en": "Helsinki-NLP/opus-mt-ru-en",
    "en-ru": "Helsinki-NLP/opus-mt-en-ru",
    "fr-de": "Helsinki-NLP/opus-mt-fr-de",
    "de-fr": "Helsinki-NLP/opus-mt-de-fr",
    "es-it": "Helsinki-NLP/opus-mt-es-it",
    "it-es": "Helsinki-NLP/opus-mt-it-es",
    "nl-sv": "Helsinki-NLP/opus-mt-nl-sv",
    "sv-nl": "Helsinki-NLP/opus-mt-sv-nl",
    "pl-ru": "Helsinki-NLP/opus-mt-pl-ru",
    "ru-pl": "Helsinki-NLP/opus-mt-ru-pl",
    "zh-ja": "Helsinki-NLP/opus-mt-zh-ja",
    "ja-zh": "Helsinki-NLP/opus-mt-ja-zh",
    "ko-ar": "Helsinki-NLP/opus-mt-ko-ar",
    "ar-ko": "Helsinki-NLP/opus-mt-ar-ko",
    "tr-da": "Helsinki-NLP/opus-mt-tr-da",
    "da-tr": "Helsinki-NLP/opus-mt-da-tr",
    "fi-no": "Helsinki-NLP/opus-mt-fi-no",
    "no-fi": "Helsinki-NLP/opus-mt-no-fi",
    "cs-el": "Helsinki-NLP/opus-mt-cs-el",
    "el-cs": "Helsinki-NLP/opus-mt-el-cs"
}

# 初始化翻译模型字典
translation_models_instances = {}

def load_translation_model(source_lang, target_lang):
    model_name = translation_models.get(f"{source_lang}-{target_lang}",
                                        f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}")

    # 开了vpn,设置代理,不然pycharm访问不了huggingface.co
    proxies = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }
    try:
        # tokenizer = MarianTokenizer.from_pretrained(model_name)
        # model = MarianMTModel.from_pretrained(model_name)
        tokenizer = MarianTokenizer.from_pretrained(model_name, proxies=proxies)
        model = MarianMTModel.from_pretrained(model_name, proxies=proxies)
        print(f"Loaded model and tokenizer for {source_lang} to {target_lang}")
        return tokenizer, model
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        raise

@csrf_exempt
def get_video_info(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_url = data.get('video_url')
            cookies = data.get('cookies')  # 获取 cookies
            video_info = download_video_and_extract_audio(video_url, cookies=cookies)
            return JsonResponse(video_info)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@csrf_exempt
def generate_subtitles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            audio_path = data.get('audio_path')
            subtitle_path = data.get('subtitle_path')  # 获取字幕路径
            target_lang = data.get('language')

            if subtitle_path:
                # 如果字幕文件已经存在，直接使用该字幕文件
                print(f"Using existing subtitle file: {subtitle_path}")
                subtitles_with_timestamps = load_subtitles_from_vtt(subtitle_path)
                print("到这了1")
                original_language = detect_subtitle_language(subtitles_with_timestamps)
                print("original_language:",original_language)
                print("到这了2")
                base_filename = os.path.splitext(os.path.basename(subtitle_path))[0]
                print("到这了3")
            elif audio_path:
                # 如果没有字幕文件，使用音频生成字幕
                print(f"Generating subtitles from audio file: {audio_path}")
                relative_audio_path = audio_path.replace('http://localhost:8000/', '')
                subtitles_with_timestamps, original_language = whisper_to_text_with_timestamps(relative_audio_path)
                base_filename = os.path.splitext(os.path.basename(relative_audio_path))[0]
                subtitle_path = f"videos/{base_filename}_source_subtitles.vtt"
                save_subtitles_to_vtt(subtitles_with_timestamps, subtitle_path)
            else:
                raise Exception("No audio or subtitle file found.")

            # 翻译字幕
            translated_subtitle_path = f"videos/{base_filename}_translated_subtitles.vtt"
            if subtitle_path:

                if original_language == target_lang:
                    shutil.copyfile(subtitle_path, translated_subtitle_path)
                    print("源字幕和目标字幕语言相同，直接复制源字幕为翻译字幕")
                else:

                    translated_subtitles_with_timestamps = translate_subtitles_with_timestamps(subtitles_with_timestamps, original_language, target_lang)
                    save_subtitles_to_vtt(translated_subtitles_with_timestamps, translated_subtitle_path)

            return JsonResponse({'translated_subtitles': translated_subtitle_path})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def download_video_and_extract_audio(video_url, cookies=None):
    """只获取视频链接并下载音频文件"""
    ydl_opts = {
        'format': 'bestaudio+bestaudio/best',  # 只下载音频
        'noplaylist': True,
        'outtmpl': 'videos/%(title)s.%(ext)s',  # 设置下载路径
        'no-check-certificate': True,

    }

    if cookies:
        ydl_opts['cookie'] = cookies

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            # 获取视频信息，但不下载视频
            info_dict = ydl.extract_info(video_url, download=False)

            video_title = info_dict['title']

            safe_video_title = sanitize_filename(video_title)  # 清理文件名


            # 获取视频流链接
            video_url = None
            for f in info_dict['formats']:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':  # 视频流
                    video_url = f['url']
                    break

            if not video_url:
                raise Exception("Video URL not found.")

            # 检查是否已有字幕文件
            subtitle_url = None
            for lang, subtitle_list in info_dict.get('subtitles').items():
                for subtitle in subtitle_list:
                    print("subtitle:", subtitle)
                    if subtitle.get('ext') == 'vtt':  # 只选择 .vtt 格式
                        subtitle_url = subtitle['url']
                        break
                if subtitle_url:
                    break

            print("subtitles_url:",subtitle_url)

            # 如果有字幕链接，下载字幕文件
            if subtitle_url:
                subtitle_path = os.path.join('videos', f"{safe_video_title}_source_subtitles.vtt")
                print(f"检测到字幕文件，正在下载: {subtitle_url}")
                with open(subtitle_path, 'wb') as f:
                    f.write(ydl.urlopen(subtitle_url).read())
                print(f"字幕文件已保存到: {subtitle_path}")

                return {'video_url': video_url, 'audio_path': None, 'subtitle_path': subtitle_path}

            # 如果没有字幕文件，下载音频
            # 获取音频URL并下载
            audio_url = None
            for f in info_dict['formats']:

                print(f)
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # 选择只有音频的格式

                    audio_url = f['url']

                    break

            if not audio_url:
                raise Exception("Audio URL not found.")

            # 下载音频
            audio_path = os.path.join('videos', f'{safe_video_title}.wav')
            ydl_opts['format'] = 'bestaudio[ext=m4a]/best'
            ydl_opts['outtmpl'] = audio_path  # 设置音频保存路径
            ydl_opts['download'] = True  # 下载音频

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([audio_url])

            # 返回视频链接和音频下载路径
            print("video_url:",video_url)
            print("audio_url:",audio_url)
            print("audio_path:",audio_path)
            return {'video_url': video_url, 'audio_path': audio_path}

    except Exception as e:
        print(f"Error during video or audio download: {str(e)}")
        raise Exception(f"Failed to extract audio or video: {str(e)}")


def whisper_to_text_with_timestamps(audio_path):
    try:
        result = whisper_model.transcribe(audio_path)
        subtitles_with_timestamps = []
        for segment in result['segments']:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            subtitles_with_timestamps.append({'start': start_time, 'end': end_time, 'text': text})
        original_language = result['language']
    except Exception as e:
        raise Exception(f"Whisper transcription failed: {str(e)}")
    return subtitles_with_timestamps, original_language

def save_subtitles_to_vtt(subtitles_with_timestamps, file_path):
    def format_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for subtitle in subtitles_with_timestamps:
            start_timestamp = format_timestamp(subtitle['start'])
            end_timestamp = format_timestamp(subtitle['end'])
            text = subtitle['text']
            f.write(f"{start_timestamp} --> {end_timestamp}\n{text}\n\n")

def translate_subtitles_with_timestamps(subtitles_with_timestamps, original_language, target_lang):
    translated_subtitles_with_timestamps = []
    tokenizer, model = load_translation_model(original_language, target_lang)

    for subtitle in subtitles_with_timestamps:
        text = subtitle['text']
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        outputs = model.generate(**inputs)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        translated_subtitles_with_timestamps.append({
            'start': subtitle['start'],
            'end': subtitle['end'],
            'text': translated_text
        })

    return translated_subtitles_with_timestamps

def sanitize_filename(filename):
    return re.sub(r'[^\w\-_.<>:"/\\|#* ]', '_', filename)

def detect_subtitle_language(subtitles_with_timestamps):
    """检测字幕文本的语言"""
    full_text = ' '.join([subtitle['text'] for subtitle in subtitles_with_timestamps])
    try:
        detected_language = detect(full_text)
        # 如果检测结果是类似于 zh-cn 的形式，只保留前两位
        if '-' in detected_language:
            detected_language = detected_language.split('-')[0]
        return detected_language
    except Exception as e:
        raise Exception(f"Failed to detect subtitle language: {str(e)}")


def load_subtitles_from_vtt(file_path):
    """从 VTT 文件中加载字幕及时间戳"""
    subtitles_with_timestamps = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        lines = [line.strip() for line in lines if line.strip()]  # 去掉空行
        i = 0
        while i < len(lines):
            if "-->" in lines[i]:  # 时间戳行
                timestamps = lines[i].split(" --> ")
                if len(timestamps) != 2:
                    raise ValueError(f"Invalid timestamp format: {lines[i]}")
                start_time = parse_timestamp(timestamps[0])
                end_time = parse_timestamp(timestamps[1])
                text = ""
                i += 1
                while i < len(lines) and "-->" not in lines[i]:  # 获取字幕内容
                    if lines[i].startswith("Kind:") or lines[i].startswith("Language:"):
                        i += 1  # 跳过元信息行
                        continue
                    text += lines[i] + " "
                    i += 1
                subtitles_with_timestamps.append({'start': start_time, 'end': end_time, 'text': text.strip()})
            else:
                i += 1
    except Exception as e:
        raise Exception(f"Failed to load subtitles from VTT: {str(e)}")

    return subtitles_with_timestamps


def parse_timestamp(timestamp):
    """将 VTT 时间戳转换为秒数"""
    try:
        parts = timestamp.split(":")
        if len(parts) == 3:  # 格式为 hh:mm:ss.sss
            hours, minutes, seconds = map(float, [parts[0], parts[1], parts[2].replace(',', '.')])
        elif len(parts) == 2:  # 格式为 mm:ss.sss
            hours = 0
            minutes, seconds = map(float, [parts[0], parts[1].replace(',', '.')])
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
        return hours * 3600 + minutes * 60 + seconds
    except Exception as e:
        raise ValueError(f"Error parsing timestamp {timestamp}: {e}")
