// Turns an axios error into a message a learner can act on.
// FastAPI sends `detail` as a string, or as a list of field errors on 422.

type ErrorLike = {
  response?: { status?: number; data?: { detail?: unknown } };
};

const FIELD_MESSAGES: [RegExp, string][] = [
  [/valid email/i, 'Email không hợp lệ.'],
  [/field required/i, 'Vui lòng điền đủ các ô bắt buộc.'],
  [/valid integer/i, 'Tuổi phải là một con số.'],
];

function fieldMessage(msg: string): string {
  const clean = msg.replace(/^Value error,\s*/i, '');
  return FIELD_MESSAGES.find(([re]) => re.test(clean))?.[1] ?? clean;
}

export function apiErrorMessage(err: unknown, fallback: string): string {
  const res = (err as ErrorLike)?.response;
  if (!res) {
    return 'Không kết nối được máy chủ. Máy chủ có thể đang khởi động (khoảng 1 phút) — đợi chút rồi thử lại.';
  }
  const detail = res.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0] as { msg?: unknown };
    if (typeof first?.msg === 'string') return fieldMessage(first.msg);
  }
  if (res.status === 429) return 'Bạn thử quá nhiều lần. Đợi 1 phút rồi thử lại nhé.';
  if (res.status && res.status >= 500) return 'Máy chủ đang gặp lỗi. Thử lại sau ít phút nhé.';
  return fallback;
}
