import base64

import requests
from Crypto.Cipher import AES

from MoocMain.log import Logger

logger = Logger(__name__).get_log()


def create_session():
    """
    创建一个带默认 User-Agent 的 requests.Session
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    })
    return session


def parse_response(response):
    """
    解析 API 响应：
    - 如果有 "code" 且为 200，返回 "data" 或完整 data
    - 如果没有 "code"，直接返回解析后的 JSON 数据
    - 解析失败时返回 None
    """
    try:
        data = response.json()

        # 如果是列表，直接返回
        if isinstance(data, list):
            return data

        # 如果包含 "code" 且为 200，返回 "data" 或完整 data
        if isinstance(data, dict):
            if "code" in data:
                if data["code"] == 200:
                    return data.get("data", data)  # 优先返回 data["data"]
                else:
                    logger.error(f"API 请求失败: {data.get('msg', '未知错误')}")
                    return None
            else:
                # 没有 "code" 字段，直接返回整个 data
                return data

        # 其他情况（如字符串、整数等），记录错误日志
        logger.error(f"API 返回未知格式: {data}")
        return None

    except ValueError:
        logger.error("解析 JSON 失败")
        return None


def parse_duration(duration: str) -> int:
    """
    将 'HH:MM:SS.sss' 或 'HH:MM:SS' 格式的 duration 转换为整数秒数。

    :param duration: 时间字符串，例如 '00:00:20.1670000' 或 '00:00:31'
    :return: 对应的总秒数（int）
    """
    h, m, s = duration.split(":")  # 拆分时、分、秒
    s = float(s)  # 处理可能的毫秒部分
    return int(float(h) * 3600 + float(m) * 60 + s)  # 转换为整数秒


def get_mp3_duration(mp3_url: str) -> float:
    """
    获取在线 MP3 文件的时长（支持 CBR 和 VBR）

    :param mp3_url: MP3 文件的 URL
    :return: MP3 时长（秒）
    """
    response = requests.get(mp3_url, stream=True)
    if response.status_code != 200:
        raise Exception("无法下载 MP3 文件")

    # 读取前 100KB 数据
    data = response.raw.read(100000)

    # MPEG 版本映射表
    mpeg_versions = {
        0b00: "MPEG-2.5",
        0b01: None,  # 保留，不使用
        0b10: "MPEG-2",
        0b11: "MPEG-1"
    }

    # 采样率表（按 MPEG 版本索引）
    sample_rates = {
        "MPEG-1": [44100, 48000, 32000, None],
        "MPEG-2": [22050, 24000, 16000, None],
        "MPEG-2.5": [11025, 12000, 8000, None]
    }

    # MP3 比特率表（仅适用于 MPEG-1 Layer III）
    bitrates = {
        "MPEG-1": [None, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
        "MPEG-2": [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]
    }

    file_size = int(response.headers.get("Content-Length", 0))
    if file_size == 0:
        raise Exception("无法获取文件大小")

    frame_count = 0
    total_bitrate = 0

    i = 0
    while i < len(data) - 4:
        # 查找 MP3 帧同步字节（0xFF Ex）
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            # 解析 MPEG 版本
            mpeg_version_id = (data[i + 1] >> 3) & 0x03
            mpeg_version = mpeg_versions.get(mpeg_version_id)
            if not mpeg_version:
                i += 1
                continue

            # 解析比特率索引
            bitrate_index = (data[i + 2] >> 4) & 0x0F
            if bitrate_index == 0 or bitrate_index >= len(bitrates[mpeg_version]):
                i += 1
                continue

            bitrate = bitrates[mpeg_version][bitrate_index] * 1000  # 转换为 bps

            # 解析采样率索引
            sample_rate_index = (data[i + 2] >> 2) & 0x03
            if sample_rate_index >= len(sample_rates[mpeg_version]):
                i += 1
                continue

            sample_rate = sample_rates[mpeg_version][sample_rate_index]

            # 计算帧大小
            padding = (data[i + 2] >> 1) & 0x01
            frame_size = int((144 * bitrate) / sample_rate + padding)

            # 统计比特率和帧数
            total_bitrate += bitrate
            frame_count += 1

            # 跳到下一个帧
            i += frame_size
        else:
            i += 1

    if frame_count == 0:
        return 0.0

    # 计算平均比特率
    avg_bitrate = total_bitrate / frame_count

    # 计算时长
    duration = (file_size * 8) / avg_bitrate
    return duration


'''
加解密
'''


def pad(text):
    """PKCS7 填充，使数据长度为 16 的倍数"""
    padding_size = 16 - len(text) % 16
    return text + chr(padding_size) * padding_size


def unpad(text):
    """去除 PKCS7 填充"""
    return text[:-ord(text[-1])]


def aes_encrypt_ecb(aes_key, plain_text):
    """
    AES-ECB 加密（Base64 编码）
    :param aes_key: 密钥
    :param plain_text: 待加密的文本
    :return: Base64 编码的密文
    """
    cipher = AES.new(aes_key, AES.MODE_ECB)
    padded_text = pad(plain_text)
    encrypted_bytes = cipher.encrypt(padded_text.encode('utf-8'))
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def aes_decrypt_ecb(aes_key, encrypted_text):
    """
    AES-ECB 解密（Base64 解码）
    :param aes_key: 密钥
    :param encrypted_text: Base64 编码的密文
    :return: 解密后的明文
    """
    cipher = AES.new(aes_key, AES.MODE_ECB)
    encrypted_bytes = base64.b64decode(encrypted_text)
    decrypted_text = cipher.decrypt(encrypted_bytes).decode('utf-8')
    return unpad(decrypted_text)
