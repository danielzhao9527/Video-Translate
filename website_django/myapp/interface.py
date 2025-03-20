import base64
import hashlib
import hmac
import json
import os
import time
import requests
import urllib
import subprocess
import json

lfasr_host = 'https://raasr.xfyun.cn/v2/api'
api_upload = '/upload'
api_get_result = '/getResult'


def get_video_duration(file_path):
    # 使用 ffprobe 获取视频时长
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    duration = float(result.stdout)
    return duration


def generate_srt(appid, secret_key, upload_file_path, output_path, txt_output_path):
    ts = str(int(time.time()))
    signa = get_signa(appid, secret_key, ts)

    # 获取视频的实际时长
    real_duration = get_video_duration(upload_file_path)

    # 上传文件
    upload_result = upload_file(appid, signa, ts, upload_file_path, real_duration)
    orderId = upload_result['content']['orderId']

    # 获取转写结果
    transcription_result = get_result(appid, signa, ts, orderId)
    print(json.dumps(transcription_result, ensure_ascii=False, indent=2))
    # 确保 transcription_result 是字典
    if isinstance(transcription_result, str):
        transcription_result = json.loads(transcription_result)
    # 解析结果并保存为 SRT 文件
    save_as_srt(transcription_result, output_path)
    # 解析结果并保存为 TXT 文件
    save_as_txt(transcription_result, txt_output_path)


def get_signa(appid, secret_key, ts):
    m2 = hashlib.md5()
    m2.update((appid + ts).encode('utf-8'))
    md5 = m2.hexdigest()
    md5 = bytes(md5, encoding='utf-8')
    signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
    signa = base64.b64encode(signa)
    return str(signa, 'utf-8')


def upload_file(appid, signa, ts, upload_file_path, real_duration):
    file_len = os.path.getsize(upload_file_path)
    file_name = os.path.basename(upload_file_path)

    param_dict = {
        'appId': appid,
        'signa': signa,
        'ts': ts,
        "fileSize": file_len,
        "fileName": file_name,
        "duration": str(int(real_duration))  # 使用实际时长
    }

    data = open(upload_file_path, 'rb').read(file_len)

    response = requests.post(url=lfasr_host + api_upload + "?" + urllib.parse.urlencode(param_dict),
                             headers={"Content-type": "application/json"}, data=data)
    return json.loads(response.text)


def get_result(appid, signa, ts, orderId):
    param_dict = {
        'appId': appid,
        'signa': signa,
        'ts': ts,
        'orderId': orderId,
        'resultType': "transfer,predict"
    }
    status = 3
    while status == 3:
        response = requests.post(url=lfasr_host + api_get_result + "?" + urllib.parse.urlencode(param_dict),
                                 headers={"Content-type": "application/json"})
        result = json.loads(response.text)
        status = result['content']['orderInfo']['status']
        if status == 4:  # 4表示完成
            break
        time.sleep(5)  # 每次请求间隔5秒

    return result





def save_as_srt(data, output_path):
    # 将 orderResult 字符串解析为字典
    order_result = json.loads(data['content']['orderResult'])
    subtitles = order_result['lattice']

    # 遍历每个字幕
    with open(output_path, 'w', encoding='utf-8') as srt_file:
        for i, subtitle in enumerate(subtitles):
            # 将 json_1best 字符串解析为字典
            json_1best = json.loads(subtitle['json_1best'])
            start_time = int(json_1best['st']['bg']) / 1000  # 转换为秒
            end_time = int(json_1best['st']['ed']) / 1000  # 转换为秒

            # 格式化时间为 SRT 所需格式
            start_time_str = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},{int((start_time - int(start_time)) * 1000):03}"
            end_time_str = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},{int((end_time - int(end_time)) * 1000):03}"

            # 获取字幕文本（假设使用 json_1best 中的内容）
            subtitle_text = ''.join([word['cw'][0]['w'] for word in json_1best['st']['rt'][0]['ws']])

            # 写入 SRT 格式
            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{start_time_str} --> {end_time_str}\n")
            srt_file.write(f"{subtitle_text}\n\n")


def format_srt_time(seconds):
    """将秒转换为 SRT 时间格式"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"


def save_as_txt(data, txt_output_path):
    """保存为不带时间戳的纯文本字幕"""
    order_result = json.loads(data['content']['orderResult'])
    subtitles = order_result['lattice']

    with open(txt_output_path, 'w', encoding='utf-8') as txt_file:
        for subtitle in subtitles:
            json_1best = json.loads(subtitle['json_1best'])
            subtitle_text = ''.join([word['cw'][0]['w'] for word in json_1best['st']['rt'][0]['ws']])
            txt_file.write(f"{subtitle_text}\n")



# 输入讯飞开放平台的appid，secret_key和待转写的文件路径
if __name__ == '__main__':
    generate_srt(
        appid="527fdc75",
        secret_key="bad22c89a7900803b7a78e7e99014eb2",
        upload_file_path=r"C:\Users\Heng\Desktop\视频\霸占母親為妻，最終被兒子割掉下體，一代神王為何做出這種事？.mp4",
        output_path=r"C:\Users\Heng\Desktop\视频\字幕\霸占母親為妻，最終被兒子割掉下體，一代神王為何做出這種事？.srt",
        txt_output_path=r"C:\Users\Heng\Desktop\视频\字幕\霸占母親為妻，最終被兒子割掉下體，一代神王為何做出這種事？.txt"
    )
