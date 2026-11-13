"""拉取分页列表，兼容服务端限制 pageSize 的情况。"""
import json


def collect_rows(fetch_page, page_size=100):
    rows = []
    seen = set()
    for page in range(1, 1001):
        response = fetch_page(page, page_size)
        if not isinstance(response, dict):
            raise RuntimeError("获取列表失败，请检查网络或重新登录")
        if response.get("code") not in (None, 200, "200"):
            raise RuntimeError("{}：{}".format(response.get("code"), response.get("msg") or "获取列表失败"))
        payload = response.get("data") if isinstance(response.get("data"), dict) else response
        batch = payload.get("rows", payload.get("records"))
        if not isinstance(batch, list):
            raise RuntimeError("列表响应格式错误")
        total = payload.get("total", response.get("total"))
        try:
            total = int(total) if total is not None else None
        except (TypeError, ValueError):
            total = None
        if not batch:
            if total is not None and len(rows) < total:
                raise RuntimeError("分页提前结束，未获取完整列表")
            return rows
        added = 0
        for item in batch:
            if not isinstance(item, dict):
                continue
            key = str(item.get("id") or item.get("courseInfoId") or json.dumps(item, sort_keys=True, ensure_ascii=False))
            if key not in seen:
                seen.add(key)
                rows.append(item)
                added += 1
        if total is not None and len(rows) >= total:
            return rows
        if not added:
            raise RuntimeError("分页未前进，无法获取完整列表")
    raise RuntimeError("分页数量超出限制")
