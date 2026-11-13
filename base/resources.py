"""兼容课件元数据和学习记录的不同响应格式。"""
import json

from base.util import get_mp3_duration, parse_duration

ASSESSMENT_TYPES = {"作业", "测验", "考试", "讨论", "topic", "子节点", "文件夹"}
VIDEO_TYPES = {"video", "mp4", "avi", "mov", "flv", "wmv", "mpg", "mpeg", "rm", "rmvb", "m4v", "webm", "mkv", "3gp", "ts"}
AUDIO_TYPES = {"audio", "mp3", "wav", "wma", "m4a", "aac", "flac", "ogg"}
DOCUMENT_TYPES = {"doc", "docx", "ppt", "pptx", "pdf", "xls", "xlsx", "txt"}


class ResourceUnavailable(ValueError):
    """平台旧课件缺少可用元数据，不能猜测时长并提交完成记录。"""


def resource_metadata(value):
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        if value.startswith(("http://", "https://")):
            return {"fileUrl": value}
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("课件元数据格式错误")


def resource_total(file_type, metadata):
    file_type = (file_type or "").lower()
    if file_type in VIDEO_TYPES | AUDIO_TYPES:
        for duration in (metadata.get("duration"), metadata.get("videoTime")):
            if duration in (None, ""):
                continue
            try:
                seconds = parse_duration(duration)
            except (TypeError, ValueError):
                continue
            if seconds > 0:
                return seconds
        if file_type in ("mp3", "audio"):
            url = metadata.get("ossOriUrl") or metadata.get("fileUrl")
            if url:
                duration = int(get_mp3_duration(url))
                if duration > 0:
                    return duration
        raise ResourceUnavailable("平台课件缺少有效时长，已跳过；不会猜测时长或标记完成")
    pages = metadata.get("page_count") or metadata.get("pageCount")
    return max(1, int(pages)) if pages else 1


def completed_resource_ids(records):
    result = set()
    for record in records:
        if isinstance(record, dict):
            record = record.get("sourceId") or record.get("coursewareId") or record.get("id")
        if record not in (None, ""):
            result.add(str(record))
    return result
