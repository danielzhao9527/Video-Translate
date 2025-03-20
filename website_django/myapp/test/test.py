import json
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError


def get_playable_formats(info_dict, prefer_audio=True):
    '''
    从信息字典中提取可播放的视频格式，并进行筛选。

    参数:
    info_dict: 提取到的 YouTube 视频信息字典。

    prefer_audio: 是否优先选择有音频的视频格式，默认为 True。

    返回:
    可播放的视频格式列表。
    '''
    if not info_dict or 'formats' not in info_dict:
        return []

    playable_formats = []

    for fmt in info_dict['formats']:
        format_id = fmt.get('format_id')
        url = fmt.get('url')
        resolution = fmt.get('height')  # 获取分辨率（如果有）
        filesize = fmt.get('filesize')
        vcodec = fmt.get('vcodec')
        acodec = fmt.get('acodec')
        ext = fmt.get('ext')
        # 跳过没有url的格式
        if not url:
            continue


        if prefer_audio and acodec != 'none':
            playable_formats.append({
                'format_id': format_id,
                'resolution': resolution,
                'ext': fmt.get('ext'),
                'url': url,
                'filesize': filesize,
                'vcodec': vcodec,
                'acodec': acodec,
            })
        elif not prefer_audio:
            # 如果不关心音频，可以选择没有音频的格式
            playable_formats.append({
                'format_id': format_id,
                'resolution': resolution,
                'ext': fmt.get('ext'),
                'url': url,
                'filesize': filesize,
                'vcodec': vcodec,
                'acodec': acodec,
            })



    return playable_formats


def extract_video_info(url):
    '''
    该函数用于提取视频信息并进行数据清理和异常处理。

    参数:
    url: 要提取信息的视频 URL。

    返回:
    清理后的视频信息字典。
    '''
    ydl_opts = {
        'cachedir': False,
        'quiet': True,
        'extract_flat': True,  # 如果是播放列表，仅返回视频列表
        'no-check-certificate': True,
        'no_warnings': False,
        'geo_bypass': True,  # 绕过地区限制
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }

    }

    result = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
    except (DownloadError, ExtractorError) as e:
        print(f"错误: {e}")
        return None  # 如果发生错误，返回 None

    # 处理提取到的数据
    if result is not None:
        # 去掉不需要的数据
        cleaned_result = {
            'title': result.get('title'),
            'description': result.get('description'),
            'url': result.get('url'),
            'id': result.get('id'),
            'duration': result.get('duration'),
            'thumbnail': result.get('thumbnail'),
            'formats': result.get('formats', []),
        }

        # 如果是播放列表，提取每个视频的信息
        if 'entries' in result:
            cleaned_result['entries'] = []
            for entry in result['entries']:
                cleaned_entry = {
                    'title': entry.get('title'),
                    'url': entry.get('url'),
                    'id': entry.get('id'),
                }
                cleaned_result['entries'].append(cleaned_entry)

        # return cleaned_result
        return result

    return None  # 如果没有结果，返回 None


def save_info_to_file(info_dict, filename='video_info.json'):
    '''    将提取到的视频信息保存到 JSON 文件中。

    参数:
    info_dict: 要保存的数据字典。
    filename: 保存文件的名称。
    '''
    if info_dict is not None:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(info_dict, f, ensure_ascii=False, indent=4)
        print(f"信息已保存到 {filename}")
    else:
        print("没有可保存的信息。")


if __name__ == '__main__':
    # url = 'https://v.youku.com/v_show/id_XNjQzNzM0MDg4NA==.html?spm=a2hja.14919748_WEBHOME_NEW.app.5~5!2~5!9~A&s=2cefbfbd6113efbfbd6c&scm=20140719.manual.29095.show_2cefbfbd6113efbfbd6c_%E9%A2%84%E8%A7%88&s=2cefbfbd6113efbfbd6c'
    # url = 'https://www.bilibili.com/video/BV1VRBBYNEsn/?vd_source=e0c4a0b1e0c2d946657bb9fc01061b7f'
    # url = 'https://www.bilibili.com/video/BV1RGz5YBEUP/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=0fa70e72f2b7200d58496236b8481962'
    url = 'https://www.youtube.com/watch?v=OI3bsOHDALs'
    # url = 'https://www.youtube.com/watch?v=rFV7wdEX-Mo'
    # url = 'https://www.twitch.tv/aspaszin'
    # url = 'https://v.youku.com/v_show/id_XNjQ0NzU1NDU2NA==.html?playMode=pugv&frommaciku=1&false'
    info_dict = extract_video_info(url)

    # print(info_dict)  # 打印提取的信息
    save_info_to_file(info_dict)  # 保存信息到文件
    playable_formats = get_playable_formats(info_dict)  # 获取可播放格式
    print("可播放的视频格式:")
    # print(playable_formats)
    for fmt in playable_formats:
        print(fmt)
