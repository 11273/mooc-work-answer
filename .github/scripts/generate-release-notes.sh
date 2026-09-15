#!/usr/bin/env bash

set -euo pipefail

TAG_NAME="${1:?用法: generate-release-notes.sh <tag> [输出文件] [上一版本tag]}"
OUTPUT_PATH="${2:-changelog.txt}"
PREV_TAG="${3:-}"
REPOSITORY="${GITHUB_REPOSITORY:-11273/mooc-work-answer}"

if [[ -z "${PREV_TAG}" ]]; then
  PREV_TAG="$(git describe --tags --abbrev=0 "${TAG_NAME}^" 2>/dev/null || true)"
fi

if [[ -n "${PREV_TAG}" ]]; then
  COMMIT_RANGE="${PREV_TAG}..${TAG_NAME}"
else
  COMMIT_RANGE="${TAG_NAME}"
fi

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

touch \
  "${WORK_DIR}/breaking" \
  "${WORK_DIR}/features" \
  "${WORK_DIR}/fixes" \
  "${WORK_DIR}/improvements" \
  "${WORK_DIR}/docs" \
  "${WORK_DIR}/engineering" \
  "${WORK_DIR}/other"

CONVENTIONAL_PATTERN='^([[:alpha:]]+)(\([^)]+\))?(!)?:[[:space:]]*(.+)$'
LEGACY_PATTERN='^\[([[:alpha:]]+)\][[:space:]]*(.+)$'
HAS_ENTRIES="false"

while IFS= read -r SUBJECT || [[ -n "${SUBJECT}" ]]; do
  [[ -z "${SUBJECT}" ]] && continue

  TYPE=""
  DESCRIPTION="${SUBJECT}"
  IS_BREAKING="false"

  if [[ "${SUBJECT}" =~ ${CONVENTIONAL_PATTERN} ]]; then
    TYPE="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
    DESCRIPTION="${BASH_REMATCH[4]}"
    [[ "${BASH_REMATCH[3]}" == "!" ]] && IS_BREAKING="true"
  elif [[ "${SUBJECT}" =~ ${LEGACY_PATTERN} ]]; then
    TYPE="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
    DESCRIPTION="${BASH_REMATCH[2]}"
  fi

  if [[ "${IS_BREAKING}" == "true" || "${TYPE}" == "breaking" ]]; then
    TARGET="breaking"
  else
    case "${TYPE}" in
      feat|feature)
        TARGET="features"
        ;;
      fix|bugfix|hotfix)
        TARGET="fixes"
        ;;
      perf|refactor|polish|style)
        TARGET="improvements"
        ;;
      docs|doc|readme)
        TARGET="docs"
        ;;
      build|ci|test|git)
        TARGET="engineering"
        ;;
      *)
        TARGET="other"
        ;;
    esac
  fi

  printf -- '- %s\n' "${DESCRIPTION}" >> "${WORK_DIR}/${TARGET}"
  HAS_ENTRIES="true"
done < <(git log "${COMMIT_RANGE}" --pretty=format:'%s' --no-merges -n 100)

write_section() {
  local title="$1"
  local file="$2"

  if [[ -s "${file}" ]]; then
    printf '### %s\n\n' "${title}"
    cat "${file}"
    printf '\n'
  fi
}

RELEASE_URL="https://github.com/${REPOSITORY}/releases/tag/${TAG_NAME}"
VIEW_COUNTER_ID="$(printf '%s-%s' "${REPOSITORY}" "${TAG_NAME}" | sed 's/[^a-zA-Z0-9-]/-/g')"

{
  printf '[![GitHub Release](https://img.shields.io/github/v/release/%s?style=flat-square&logo=github&color=blue)](%s) ' "${REPOSITORY}" "${RELEASE_URL}"
  printf '[![下载统计](https://img.shields.io/github/downloads/%s/%s/total?style=flat-square&logo=github&color=green)](%s) ' "${REPOSITORY}" "${TAG_NAME}" "${RELEASE_URL}"
  printf '[![访问统计](https://komarev.com/ghpvc/?username=%s&label=Views&style=flat-square&color=brightgreen)](%s)\n\n' "${VIEW_COUNTER_ID}" "${RELEASE_URL}"
  printf '## 🚀 版本更新 %s\n\n' "${TAG_NAME}"
  printf '## 📋 更新内容\n\n'

  write_section '⚠️ 破坏性变更' "${WORK_DIR}/breaking"
  write_section '✨ 新增功能' "${WORK_DIR}/features"
  write_section '🐛 问题修复' "${WORK_DIR}/fixes"
  write_section '⚡ 优化调整' "${WORK_DIR}/improvements"
  write_section '📝 文档更新' "${WORK_DIR}/docs"
  write_section '🛠️ 工程构建' "${WORK_DIR}/engineering"
  write_section '📌 其他更新' "${WORK_DIR}/other"

  if [[ "${HAS_ENTRIES}" == "false" ]]; then
    printf -- '- 本版本暂无可展示的提交记录\n\n'
  fi

  printf '### 📦 支持平台\n\n'
  printf -- '- 🪟 **Windows**: 支持 Windows 7/8/10/11 (x64)\n'
  printf -- '- 🍎 **macOS**: 支持 macOS 10.14+ (Intel & Apple Silicon)\n'
  printf -- '- 🐧 **Linux**: 支持主流 Linux 发行版 (x64)\n\n'
  printf '### 💾 下载说明\n\n'
  printf -- '- **Windows**: 直接下载 `.exe` 文件运行\n'
  printf -- '- **macOS**: 直接下载可执行文件，通过终端运行\n'
  printf -- '- **Linux**: 直接下载可执行文件运行\n\n'
  printf '### 🔧 使用方法\n\n'
  printf '1. 根据您的系统下载对应版本（无需解压）\n'
  printf '2. **Windows**: 双击运行 `.exe` 文件\n'
  printf '3. **macOS**: 打开终端，拖拽文件到终端窗口，然后按回车\n'
  printf '4. **Linux**: 在终端中运行 `./filename`\n'
  printf '5. 按照提示选择需要的功能开始使用\n\n'
  printf '### 💡 macOS 使用提示\n\n'
  printf -- '- 下载后如果出现权限错误，先运行：`chmod +x filename`\n'
  printf -- '- 然后直接拖拽文件到终端窗口即可运行\n'
  printf -- '- 或在终端中进入文件所在目录，再运行 `./filename`\n'
} > "${OUTPUT_PATH}"

printf '更新日志已生成：%s（范围：%s）\n' "${OUTPUT_PATH}" "${COMMIT_RANGE}"
