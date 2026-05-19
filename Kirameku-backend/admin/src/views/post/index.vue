<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "@/utils/message";
import { getPosts, deletePost, getPostCount } from "@/api/post";
import type { PostItem } from "@/api/post";
import { getCategories } from "@/api/category";
import type { CategoryItem } from "@/api/category";
import { getTags } from "@/api/tag";
import type { TagItem } from "@/api/tag";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import type { PaginationProps } from "@pureadmin/table";
import ArticleLine from "~icons/ri/article-line";
import CheckboxCircleLine from "~icons/ri/checkbox-circle-line";
import DraftLine from "~icons/ri/draft-line";
import ArchiveLine from "~icons/ri/archive-line";
import EyeLine from "~icons/ri/eye-line";
import HeartLine from "~icons/ri/heart-line";
import PushpinFill from "~icons/ri/pushpin-fill";
import CalendarLine from "~icons/ri/calendar-line";

defineOptions({ name: "PostIndex" });

const router = useRouter();
const loading = ref(false);
const dataList = ref<PostItem[]>([]);
const selectedRows = ref<PostItem[]>([]);
const keyword = ref("");
const statusFilter = ref("");
const categoryFilter = ref("");
const tagFilter = ref("");
const categoryList = ref<CategoryItem[]>([]);
const tagList = ref<TagItem[]>([]);

const stats = reactive({ total: 0, published: 0, draft: 0, archived: 0 });

const pagination = reactive<PaginationProps>({
  total: 0,
  pageSize: 20,
  currentPage: 1,
  background: true
});

const columns: TableColumnList = [
  { type: "selection", width: 40, reserveSelection: true },
  { label: "文章", prop: "title", minWidth: 300, slot: "article" },
  { label: "分类", prop: "category", width: 110, slot: "category" },
  { label: "标签", prop: "tags", minWidth: 150, slot: "tags" },
  { label: "状态", prop: "status", width: 100, slot: "status" },
  { label: "数据", prop: "views", width: 120, slot: "data" },
  { label: "发布时间", prop: "published_at", minWidth: 170, slot: "time" },
  { label: "操作", width: 150, slot: "operation" }
];

const hasSelection = computed(() => selectedRows.value.length > 0);

const statCards = computed(() => [
  { key: "", label: "全部文章", value: stats.total, icon: ArticleLine, color: "#409eff", bg: "#ecf5ff" },
  { key: "published", label: "已发布", value: stats.published, icon: CheckboxCircleLine, color: "#67c23a", bg: "#f0f9eb" },
  { key: "draft", label: "草稿箱", value: stats.draft, icon: DraftLine, color: "#909399", bg: "#f4f4f5" },
  { key: "archived", label: "已归档", value: stats.archived, icon: ArchiveLine, color: "#e6a23c", bg: "#fdf6ec" }
]);

async function loadFilters() {
  const [cats, tags] = await Promise.all([
    getCategories().catch(() => []),
    getTags().catch(() => [])
  ]);
  categoryList.value = cats;
  tagList.value = tags;
}

async function onSearch() {
  loading.value = true;
  try {
    const params: any = { page: pagination.currentPage, size: pagination.pageSize };
    if (statusFilter.value) params.status = statusFilter.value;
    if (categoryFilter.value) params.category = categoryFilter.value;
    if (tagFilter.value) params.tag = tagFilter.value;
    const [list, countRes] = await Promise.all([
      getPosts(params),
      getPostCount({ status: statusFilter.value || undefined })
    ]);
    dataList.value = list;
    pagination.total = countRes.count;
  } finally {
    loading.value = false;
  }
}

async function loadStats() {
  try {
    const [all, published, draft, archived] = await Promise.all([
      getPostCount(),
      getPostCount({ status: "published" }),
      getPostCount({ status: "draft" }),
      getPostCount({ status: "archived" })
    ]);
    stats.total = all.count;
    stats.published = published.count;
    stats.draft = draft.count;
    stats.archived = archived.count;
  } catch { /* ignore */ }
}

function handleSearch() {
  pagination.currentPage = 1;
  onSearch();
}

function handleReset() {
  keyword.value = "";
  statusFilter.value = "";
  categoryFilter.value = "";
  tagFilter.value = "";
  pagination.currentPage = 1;
  onSearch();
}

function handleSizeChange(val: number) {
  pagination.pageSize = val;
  pagination.currentPage = 1;
  onSearch();
}

function handleCurrentChange(val: number) {
  pagination.currentPage = val;
  onSearch();
}

function handleEdit(row: PostItem) {
  router.push(`/post/edit/${row.id}`);
}

function handleCreate() {
  router.push("/post/edit");
}

async function handleDelete(row: PostItem) {
  try {
    await deletePost(row.id);
    message("删除成功", { type: "success" });
    onSearch();
    loadStats();
  } catch (e: any) {
    message(e?.message ?? "删除失败", { type: "error" });
  }
}

async function handleBatchDelete() {
  if (!selectedRows.value.length) return;
  try {
    await Promise.all(selectedRows.value.map(row => deletePost(row.id)));
    message(`成功删除 ${selectedRows.value.length} 篇文章`, { type: "success" });
    selectedRows.value = [];
    onSearch();
    loadStats();
  } catch (e: any) {
    message(e?.message ?? "批量删除失败", { type: "error" });
  }
}

function handleSelectionChange(rows: PostItem[]) {
  selectedRows.value = rows;
}

function formatTime(t: string | null | undefined) {
  if (!t) return "-";
  return t.replace("T", " ").slice(0, 16);
}

onMounted(() => {
  loadFilters();
  onSearch();
  loadStats();
});
</script>

<template>
  <div class="post-page">
    <div class="post-header">
      <div class="header-info">
        <h2 class="page-title">文章管理</h2>
        <p class="page-desc">管理和发布你的博客文章</p>
      </div>
      <el-button
        type="primary"
        :icon="useRenderIcon('ri:add-circle-line')"
        size="large"
        round
        @click="handleCreate"
      >
        写文章
      </el-button>
    </div>

    <div class="post-stats">
      <div
        v-for="card in statCards"
        :key="card.key"
        class="stat-card"
        :class="{ active: statusFilter === card.key }"
        @click="statusFilter = card.key; handleSearch()"
      >
        <div class="stat-left" :style="{ borderLeftColor: card.color }">
          <div class="stat-icon" :style="{ color: card.color, background: card.bg }">
            <IconifyIconOffline :icon="card.icon" />
          </div>
          <div class="stat-body">
            <div class="stat-num" :style="{ color: card.color }">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="post-table-card">
      <div class="post-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="keyword"
            placeholder="搜索文章标题..."
            clearable
            class="search-input"
            :prefix-icon="useRenderIcon('ri:search-line')"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-select
            v-model="categoryFilter"
            placeholder="选择分类"
            clearable
            class="filter-select"
            @change="handleSearch"
          >
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.name"
            />
          </el-select>
          <el-select
            v-model="tagFilter"
            placeholder="选择标签"
            clearable
            class="filter-select"
            @change="handleSearch"
          >
            <el-option
              v-for="tag in tagList"
              :key="tag.id"
              :label="tag.name"
              :value="tag.name"
            />
          </el-select>
          <el-button :icon="useRenderIcon('ri:refresh-line')" @click="handleReset">
            重置
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-button
            v-if="hasSelection"
            type="danger"
            plain
            round
            :icon="useRenderIcon('ri:delete-bin-line')"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRows.length }})
          </el-button>
        </div>
      </div>

      <pure-table
        :data="dataList"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        align-whole="center"
        row-key="id"
        table-layout="auto"
        @selection-change="handleSelectionChange"
        @page-size-change="handleSizeChange"
        @page-current-change="handleCurrentChange"
      >
        <template #article="{ row }">
          <div class="article-cell">
            <div class="article-title" @click="handleEdit(row)">
              <IconifyIconOffline
                v-if="row.is_pinned"
                :icon="PushpinFill"
                class="pin-icon"
              />
              {{ row.title }}
            </div>
            <div v-if="row.description" class="article-desc">{{ row.description }}</div>
            <div class="article-meta">
              <span v-if="row.is_pinned" class="meta-pin">置顶</span>
              <span>{{ row.word_count ?? 0 }} 字</span>
              <span class="meta-dot">·</span>
              <span>约 {{ row.reading_time ?? 0 }} 分钟阅读</span>
            </div>
          </div>
        </template>

        <template #category="{ row }">
          <el-tag
            v-if="row.category"
            effect="plain"
            round
            size="small"
          >
            {{ row.category }}
          </el-tag>
          <span v-else class="text-placeholder">-</span>
        </template>

        <template #tags="{ row }">
          <div class="tags-cell">
            <el-tag
              v-for="tag in (row.tags || []).slice(0, 3)"
              :key="tag"
              size="small"
              effect="plain"
              round
              type="info"
            >
              {{ tag }}
            </el-tag>
            <el-tag
              v-if="(row.tags || []).length > 3"
              size="small"
              effect="plain"
              round
              type="info"
            >
              +{{ row.tags.length - 3 }}
            </el-tag>
          </div>
        </template>

        <template #status="{ row }">
          <span
            class="status-dot-wrap"
            :class="row.status"
          >
            <span class="dot" />
            {{ row.status === "published" ? "已发布" : row.status === "draft" ? "草稿" : "已归档" }}
          </span>
        </template>

        <template #data="{ row }">
          <div class="data-cell">
            <span class="data-item">
              <IconifyIconOffline :icon="EyeLine" class="data-icon" />
              {{ row.views ?? 0 }}
            </span>
            <span class="data-item data-likes">
              <IconifyIconOffline :icon="HeartLine" class="data-icon" />
              {{ row.likes ?? 0 }}
            </span>
          </div>
        </template>

        <template #time="{ row }">
          <div class="time-cell">
            <div v-if="row.published_at" class="time-row">
              <IconifyIconOffline :icon="CalendarLine" class="time-icon" />
              {{ formatTime(row.published_at) }}
            </div>
            <div v-else class="text-placeholder">未发布</div>
            <div v-if="row.updated_at" class="time-sub">
              更新于 {{ formatTime(row.updated_at) }}
            </div>
          </div>
        </template>

        <template #operation="{ row }">
          <div class="op-cell">
            <el-button
              link
              type="primary"
              :icon="useRenderIcon('ri:edit-line')"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-popconfirm :title="`确认删除「${row.title}」？`" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" :icon="useRenderIcon('ri:delete-bin-line')">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </template>
      </pure-table>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.post-page {
  padding: 20px;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
  line-height: 1.3;
}

.page-desc {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 4px 0 0;
}

.post-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 10px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.25s ease;
  overflow: hidden;

  &:hover {
    box-shadow: 0 4px 16px rgb(0 0 0 / 6%);
    transform: translateY(-1px);
  }

  &.active {
    box-shadow: 0 4px 16px rgb(0 0 0 / 8%);
  }
}

.stat-left {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-left: 3px solid transparent;
  transition: border-color 0.25s;
}

.stat-card.active .stat-left {
  border-left-width: 3px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  font-size: 20px;
  flex-shrink: 0;
  transition: transform 0.25s;
}

.stat-card:hover .stat-icon {
  transform: scale(1.08);
}

.stat-body {
  .stat-num {
    font-size: 24px;
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -0.5px;
  }

  .stat-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
  }
}

.post-table-card {
  border-radius: 10px;

  :deep(.el-card__body) {
    padding: 0;
  }
}

.post-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.toolbar-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  width: 220px;
}

.filter-select {
  width: 120px;
}

.article-cell {
  text-align: left;

  .article-title {
    font-weight: 600;
    font-size: 14px;
    color: var(--el-text-color-primary);
    cursor: pointer;
    line-height: 1.5;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: color 0.2s;

    &:hover {
      color: var(--el-color-primary);
    }

    .pin-icon {
      color: #e6a23c;
      font-size: 14px;
      flex-shrink: 0;
    }
  }

  .article-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .article-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    font-size: 12px;
    color: var(--el-text-color-placeholder);

    .meta-pin {
      color: #e6a23c;
      font-weight: 600;
    }

    .meta-dot {
      color: var(--el-border-color);
    }
  }
}

.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.status-dot-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  &.published {
    color: #67c23a;
    .dot { background: #67c23a; }
  }

  &.draft {
    color: #909399;
    .dot { background: #909399; }
  }

  &.archived {
    color: #e6a23c;
    .dot { background: #e6a23c; }
  }
}

.data-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;

  .data-item {
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 13px;
    color: var(--el-text-color-regular);
  }

  .data-icon {
    font-size: 14px;
    color: var(--el-text-color-placeholder);
  }

  .data-likes .data-icon {
    color: #f56c6c;
  }
}

.text-placeholder {
  color: var(--el-text-color-placeholder);
}

.time-cell {
  text-align: left;

  .time-row {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 13px;
    color: var(--el-text-color-regular);
    font-weight: 500;
  }

  .time-icon {
    font-size: 14px;
    color: var(--el-text-color-placeholder);
    flex-shrink: 0;
  }

  .time-sub {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
    margin-top: 3px;
    padding-left: 19px;
  }
}

.op-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

html.dark .stat-card {
  border-color: rgb(255 255 255 / 8%);

  &:hover {
    box-shadow: 0 4px 16px rgb(0 0 0 / 25%);
  }

  &.active {
    box-shadow: 0 4px 16px rgb(0 0 0 / 30%);
  }
}

@media screen and (width <= 768px) {
  .post-page {
    padding: 12px;
  }

  .post-header {
    margin-bottom: 16px;
  }

  .page-title {
    font-size: 18px;
  }

  .page-desc {
    font-size: 12px;
  }

  .post-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }

  .stat-left {
    padding: 14px 16px;
    gap: 10px;
  }

  .stat-icon {
    width: 38px;
    height: 38px;
    font-size: 17px;
    border-radius: 8px;
  }

  .stat-body .stat-num {
    font-size: 20px;
  }

  .post-toolbar {
    padding: 12px 14px;
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    width: 100%;
  }

  .toolbar-left {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    width: 100%;
  }

  .filter-select {
    width: 100%;
  }
}

@media screen and (width <= 480px) {
  .post-page {
    padding: 8px;
  }

  .post-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .post-stats {
    gap: 8px;
  }

  .stat-left {
    padding: 12px;
    gap: 8px;
  }

  .stat-icon {
    width: 34px;
    height: 34px;
    font-size: 15px;
  }

  .stat-body {
    .stat-num {
      font-size: 18px;
    }

    .stat-label {
      font-size: 12px;
    }
  }
}
</style>
