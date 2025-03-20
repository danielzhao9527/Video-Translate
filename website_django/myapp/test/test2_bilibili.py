import yt_dlp


def get_playable_links(video_url):
    """
    获取包含视频和音频的可播放链接。

    :param video_url: 视频链接
    :return: 包含视频标题及可播放链接的字典
    """
    ydl_opts = {
        'cachedir': False,
        'quiet': False,  # 显示详细信息
        'verbose': True,  # 打印调试日志
        'geo_bypass': True,  # 绕过地区限制
        'cookiefile': r'bilibili.com_cookies.txt',  # 替换为你的 Cookies 文件路径
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'Unknown Title')
            playable_links = []

            for fmt in info.get('formats', []):
                if fmt.get('vcodec', 'none') != 'none' and fmt.get('acodec', 'none') != 'none':
                    playable_links.append({
                        'format_id': fmt['format_id'],
                        'resolution': fmt.get('resolution', f"{fmt.get('width')}x{fmt.get('height')}"),
                        'filesize': fmt.get('filesize', 'Unknown'),
                        'url': fmt['url'],
                        'ext': fmt['ext'],
                    })

            return {'title': video_title, 'links': playable_links}
        except Exception as e:
            return {'error': str(e)}


# 示例用法
if __name__ == "__main__":
    url = 'https://www.bilibili.com/video/BV1VRBBYNEsn'
    result = get_playable_links(url)
    if 'error' in result:
        print(f"解析失败: {result['error']}")
    else:
        print("视频标题:", result['title'])
        print("可播放链接:")
        for link in result['links']:
            print(
                f"- 格式ID: {link['format_id']}, 分辨率: {link['resolution']}, 类型: {link['ext']}, 链接: {link['url']}")
