// src/utils/date.js

/**
 * 将 UTC 字符串自动转换为用户“当前手机/电脑设备”本地时区的时间，并支持自定义格式
 * @param {string} isoString - 后端返回的 UTC 字符串，如 "2026-06-27T06:10:00Z"
 * @param {string} pattern - 期望输出的格式，默认 "MM-DD HH:mm"
 * @returns {string} 格式化后的本地时区时间
 */
export function formatLocalTime(isoString, pattern = "MM-DD HH:mm") {
  if (!isoString) return "";
  try {
    const date = new Date(isoString);
    // 如果传入的不是有效的时间格式，则原样返回，防止程序崩溃
    if (isNaN(date.getTime())) return isoString; 

    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    const ss = String(date.getSeconds()).padStart(2, '0');

    // 根据传入的 pattern，动态替换字母
    return pattern
      .replace("YYYY", yyyy)
      .replace("MM", mm)
      .replace("DD", dd)
      .replace("HH", hh)
      .replace("mm", min)
      .replace("ss", ss);
  } catch (err) {
    console.error("时间转换出错:", err);
    return isoString;
  }
}