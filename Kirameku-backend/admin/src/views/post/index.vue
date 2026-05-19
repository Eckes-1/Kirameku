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
  { label: "文章", prop: "title", minWidth: 260, slot: "article" },
  { label: "分类", prop: "category", width: 100, slot: "category" },
  { label: "标签", prop: "tags", minWidth: 140, slot: "tags" },
  { label: "状态", prop: "status", width: 80, slot: "status" },
  { label: "浏览", prop: "views", width: 70, formatter: ({ views }) => views ?? 0 },
  { label: "点赞", prop: "likes", width: 70, formatter: ({ likes }) => likes ?? 0 },
  { label: "发布时间", prop: "published_at", minWidth: 150, slot: "time" },
  { label: "操作", width: 140, slot: "operation" }
];

const hasSelection = computed(() => selectedRows.value.length > 0);

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
        class="stat-card"
        :class="{ active: statusFilter === '' }"
        @click="statusFilter = ''; handleSearch()"
      >
        <div class="stat-num">{{ stats.total }}</div>
        <div class="stat-label">全部文章</div>
      </div>
      <div
        class="stat-card stat-published"
        :class="{ active: statusFilter === 'published' }"
        @click="statusFilter = 'published'; handleSearch()"
      >
        <div class="stat-num">{{ stats.published }}</div>
        <div class="stat-label">已发布</div>
      </div>
      <div
        class="stat-card stat-draft"
        :class="{ active: statusFilter === 'draft' }"
        @click="statusFilter = 'draft'; handleSearch()"
      >
        <div class="stat-num">{{ stats.draft }}</div>
        <div class="stat-label">草稿</div>
      </div>
      <div
        class="stat-card stat-archived"
        :class="{ active: statusFilter === 'archived' }"
        @click="statusFilter = 'archived'; handleSearch()"
      >
        <div class="stat-num">{{ stats.archived }}</div>
        <div class="stat-label">已归档</div>
      </div>
    </div>

    <el-card shadow="never" class="post-table-card">
      <div class="post-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="keyword"
            placeholder="搜索文章..."
            clearable
            class="search-input"
            :prefix-icon="useRenderIcon('ri:search-line')"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-select
            v-model="categoryFilter"
            placeholder="分类"
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
            placeholder="标签"
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
            删除({{ selectedRows.length }})
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
              {{ row.title }}
            </div>
            <div v-if="row.description" class="article-desc">{{ row.description }}</div>
            <div class="article-meta">
              <el-tag v-if="row.is_pinned" size="small" type="warning" effect="plain" round>置顶</el-tag>
              <span>{{ row.word_count ?? 0 }} 字</span>
              <span>约 {{ row.reading_time ?? 0 }} 分钟</span>
            </div>
          </div>
        </template>

        <template #category="{ row }">
          <span v-if="row.category">{{ row.category }}</span>
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
          <el-tag
            :type="row.status === 'published' ? 'success' : row.status === 'draft' ? 'info' : 'warning'"
            size="small"
            effect="dark"
            round
          >
            {{ row.status === "published" ? "已发布" : row.status === "draft" ? "草稿" : "已归档" }}
          </el-tag>
        </template>

        <template #time="{ row }">
          <div class="time-cell">
            <div v-if="row.published_at">{{ formatTime(row.published_at) }}</div>
            <div v-else class="text-placeholder">未发布</div>
            <div v-if="row.updated_at" class="time-sub">更新 {{ formatTime(row.updated_at) }}</div>
          </div>
        </template>

        <template #operation="{ row }">
          <el-button link type="primary" :icon="useRenderIcon('ri:edit-line')" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-popconfirm :title="`确认删除「${row.title}」？`" @confirm="handleDelete(row)">
            <template #reference>
              <el-button link type="danger" :icon="useRenderIcon('ri:delete-bin-line')">删除</el-button>
            </template>
          </el-popconfirm>
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
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  padding: 16px;
  border-radius: 8px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;

  &:hover {
    border-color: var(--el-color-primary-light-5);
  }

  &.active {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }

  .stat-num {
    font-size: 28px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    line-height: 1.2;
  }

  .stat-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }
}

.stat-published.active {
  border-color: var(--el-color-success);
  background: var(--el-color-success-light-9);
}

.stat-draft.active {
  border-color: var(--el-color-info);
  background: var(--el-color-info-light-9);
}

.stat-archived.active {
  border-color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}

.post-table-card {
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
  padding: 14px 16px;
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
  width: 200px;
}

.filter-select {
  width: 110px;
}

.article-cell {
  text-align: left;

  .article-title {
    font-weight: 600;
    font-size: 14px;
    color: var(--el-text-color-primary);
    cursor: pointer;
    line-height: 1.4;

    &:hover {
      color: var(--el-color-primary);
    }
  }

  .article-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 3px;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .article-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
    font-size: 12px;
    color: var(--el-text-color-placeholder);
  }
}

.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.text-placeholder {
  color: var(--el-text-color-placeholder);
}

.time-cell {
  text-align: left;
  font-size: 13px;
  line-height: 1.5;
  color: var(--el-text-color-regular);

  .time-sub {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
  }
}

@media screen and (width <= 768px) {
  .post-page {
    padding: 8px;
  }

  .post-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-bottom: 12px;
  }

  .stat-card {
    padding: 12px;

    .stat-num {
      font-size: 22px;
    }
  }

  .post-toolbar {
    padding: 10px 12px;
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
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }

  .stat-card {
    padding: 10px;

    .stat-num {
      font-size: 20px;
    }

    .stat-label {
      font-size: 12px;
    }
  }
}
</style>
