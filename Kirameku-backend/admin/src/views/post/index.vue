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
  { label: "文章", prop: "title", minWidth: 280, slot: "article" },
  { label: "分类", prop: "category", width: 110, slot: "category" },
  { label: "标签", prop: "tags", minWidth: 150, slot: "tags" },
  { label: "状态", prop: "status", width: 90, slot: "status" },
  { label: "浏览", prop: "views", width: 80, slot: "views" },
  { label: "点赞", prop: "likes", width: 80, slot: "likes" },
  { label: "发布时间", prop: "published_at", minWidth: 160, slot: "time" },
  { label: "操作", width: 150, slot: "operation" }
];

const hasSelection = computed(() => selectedRows.value.length > 0);

const statCards = computed(() => [
  {
    key: "",
    label: "全部文章",
    value: stats.total,
    icon: ArticleLine,
    gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    shadow: "0 4px 14px rgb(102 126 234 / 35%)"
  },
  {
    key: "published",
    label: "已发布",
    value: stats.published,
    icon: CheckboxCircleLine,
    gradient: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    shadow: "0 4px 14px rgb(67 233 123 / 35%)"
  },
  {
    key: "draft",
    label: "草稿箱",
    value: stats.draft,
    icon: DraftLine,
    gradient: "linear-gradient(135deg, #a8b8d8 0%, #8e9eab 100%)",
    shadow: "0 4px 14px rgb(142 158 171 / 35%)"
  },
  {
    key: "archived",
    label: "已归档",
    value: stats.archived,
    icon: ArchiveLine,
    gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    shadow: "0 4px 14px rgb(245 87 108 / 35%)"
  }
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
    <div class="post-stats">
      <div
        v-for="card in statCards"
        :key="card.key"
        class="stat-card"
        :class="{ active: statusFilter === card.key }"
        @click="statusFilter = card.key; handleSearch()"
      >
        <div class="stat-icon-wrap" :style="{ background: card.gradient, boxShadow: card.shadow }">
          <IconifyIconOffline :icon="card.icon" />
        </div>
        <div class="stat-body">
          <div class="stat-num">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="post-table-card">
      <div class="post-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="keyword"
            placeholder="搜索文章标题或内容..."
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
            :icon="useRenderIcon('ri:delete-bin-line')"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRows.length }})
          </el-button>
          <el-button
            type="primary"
            :icon="useRenderIcon('ri:add-circle-line')"
            @click="handleCreate"
          >
            写文章
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
              <span class="meta-item">
                <IconifyIconOffline :icon="EyeLine" class="meta-icon" />
                {{ row.views ?? 0 }}
              </span>
              <span class="meta-item">
                <IconifyIconOffline :icon="HeartLine" class="meta-icon" />
                {{ row.likes ?? 0 }}
              </span>
              <span class="meta-divider">|</span>
              <span>{{ row.word_count ?? 0 }} 字</span>
              <span>约 {{ row.reading_time ?? 0 }} 分钟</span>
            </div>
          </div>
        </template>

        <template #category="{ row }">
          <el-tag
            v-if="row.category"
            effect="plain"
            round
            class="category-tag"
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
              class="post-tag"
            >
              {{ tag }}
            </el-tag>
            <el-tag
              v-if="(row.tags || []).length > 3"
              size="small"
              effect="plain"
              type="info"
              round
            >
              +{{ row.tags.length - 3 }}
            </el-tag>
          </div>
        </template>

        <template #status="{ row }">
          <div
            class="status-badge"
            :class="row.status"
          >
            <span class="status-dot" />
            {{ row.status === "published" ? "已发布" : row.status === "draft" ? "草稿" : "已归档" }}
          </div>
        </template>

        <template #views="{ row }">
          <div class="count-cell">
            <IconifyIconOffline :icon="EyeLine" class="count-icon" />
            {{ row.views ?? 0 }}
          </div>
        </template>

        <template #likes="{ row }">
          <div class="count-cell likes">
            <IconifyIconOffline :icon="HeartLine" class="count-icon" />
            {{ row.likes ?? 0 }}
          </div>
        </template>

        <template #time="{ row }">
          <div class="time-cell">
            <div v-if="row.published_at" class="time-main">{{ formatTime(row.published_at) }}</div>
            <div v-else class="text-placeholder">未发布</div>
            <div v-if="row.updated_at" class="time-sub">更新于 {{ formatTime(row.updated_at) }}</div>
          </div>
        </template>

        <template #operation="{ row }">
          <div class="operation-cell">
            <el-tooltip content="编辑文章" placement="top">
              <el-button
                link
                type="primary"
                :icon="useRenderIcon('ri:edit-line')"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
            </el-tooltip>
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
  padding: 16px;
}

.post-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    opacity: 0.04;
    transform: translate(20px, -20px);
    transition: all 0.3s ease;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgb(0 0 0 / 8%);
  }

  &.active {
    border-color: transparent;
    transform: translateY(-2px);
  }
}

.stat-card:nth-child(1) {
  &::after { background: #667eea; }
  &.active { box-shadow: 0 8px 24px rgb(102 126 234 / 25%); }
}

.stat-card:nth-child(2) {
  &::after { background: #43e97b; }
  &.active { box-shadow: 0 8px 24px rgb(67 233 123 / 25%); }
}

.stat-card:nth-child(3) {
  &::after { background: #8e9eab; }
  &.active { box-shadow: 0 8px 24px rgb(142 158 171 / 25%); }
}

.stat-card:nth-child(4) {
  &::after { background: #f5576c; }
  &.active { box-shadow: 0 8px 24px rgb(245 87 108 / 25%); }
}

.stat-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
}

.stat-body {
  .stat-num {
    font-size: 26px;
    font-weight: 800;
    color: var(--el-text-color-primary);
    line-height: 1.2;
    letter-spacing: -0.5px;
  }

  .stat-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
    font-weight: 500;
  }
}

.post-table-card {
  border-radius: 12px;

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
  background: var(--el-bg-color);
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
      color: #f5576c;
      font-size: 14px;
      flex-shrink: 0;
      animation: pin-bounce 2s ease-in-out infinite;
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
    gap: 8px;
    margin-top: 6px;
    font-size: 12px;
    color: var(--el-text-color-placeholder);

    .meta-item {
      display: flex;
      align-items: center;
      gap: 3px;
    }

    .meta-icon {
      font-size: 13px;
    }

    .meta-divider {
      color: var(--el-border-color);
    }
  }
}

.category-tag {
  font-weight: 500;
}

.post-tag {
  transition: transform 0.2s;

  &:hover {
    transform: scale(1.05);
  }
}

.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &.published {
    background: rgb(67 233 123 / 10%);
    color: #43e97b;

    .status-dot {
      background: #43e97b;
      box-shadow: 0 0 6px #43e97b;
    }
  }

  &.draft {
    background: rgb(142 158 171 / 10%);
    color: #8e9eab;

    .status-dot {
      background: #8e9eab;
    }
  }

  &.archived {
    background: rgb(245 87 108 / 10%);
    color: #f5576c;

    .status-dot {
      background: #f5576c;
    }
  }
}

.count-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 13px;
  color: var(--el-text-color-regular);

  .count-icon {
    font-size: 14px;
    color: var(--el-text-color-placeholder);
  }

  &.likes .count-icon {
    color: #f5576c;
  }
}

.text-placeholder {
  color: var(--el-text-color-placeholder);
}

.time-cell {
  text-align: left;
  font-size: 13px;
  line-height: 1.5;

  .time-main {
    color: var(--el-text-color-regular);
    font-weight: 500;
  }

  .time-sub {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
    margin-top: 2px;
  }
}

.operation-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

@keyframes pin-bounce {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-8deg); }
  75% { transform: rotate(8deg); }
}

html.dark .stat-card {
  border-color: rgb(255 255 255 / 8%);

  &:hover {
    box-shadow: 0 8px 24px rgb(0 0 0 / 30%);
  }
}

html.dark .status-badge {
  &.published {
    background: rgb(67 233 123 / 15%);
  }

  &.draft {
    background: rgb(142 158 171 / 15%);
  }

  &.archived {
    background: rgb(245 87 108 / 15%);
  }
}

@media screen and (width <= 768px) {
  .post-page {
    padding: 10px;
  }

  .post-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }

  .stat-card {
    padding: 14px;
    gap: 12px;
  }

  .stat-icon-wrap {
    width: 40px;
    height: 40px;
    font-size: 18px;
    border-radius: 10px;
  }

  .stat-body .stat-num {
    font-size: 22px;
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
  .post-stats {
    gap: 8px;
  }

  .stat-card {
    padding: 12px;
    gap: 10px;
  }

  .stat-icon-wrap {
    width: 36px;
    height: 36px;
    font-size: 16px;
    border-radius: 8px;
  }

  .stat-body {
    .stat-num {
      font-size: 20px;
    }

    .stat-label {
      font-size: 12px;
    }
  }
}
</style>
