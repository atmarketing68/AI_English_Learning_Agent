/** Cẩm nang học: danh sách bài viết (thứ tự hiển thị trên trang /cam-nang). */
import type { Article } from './articleTypes';
import { EXAM_ARTICLES } from './articlesExam';
import { GENERAL_ARTICLES } from './articlesGeneral';

export const ARTICLES: Article[] = [...EXAM_ARTICLES, ...GENERAL_ARTICLES];
export const ARTICLE_BY_SLUG: Record<string, Article> = Object.fromEntries(ARTICLES.map(a => [a.slug, a]));
