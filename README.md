# Simple IR System

清华大学《信息检索》（孙茂松）的作业。一个支持布尔查询的信息检索demo。应用于人民日报 2000 年至 2015 年的文章。

## 环境

使用：Python + Flask + Vue + Elasticsearch

但是 Vue 是从 unpkg.com 载入的，不需要安装。

## 项目结构

代码主要分为 4 部分，全都位于 `src` 目录下：

1. 预处理：`preprocess.py` 和 `preprocess`
2. 后端：`backend`
3. 前端：`frontend`
4. 文章相似性：`sbert`

## 执行

### 1 预处理

将数据放在 `data` 目录下，然后将 Elasticsearch 跑起来。然后在 `src` 目录下执行 `python preprocess.py`。将会生成必要的处理后的数据，存到 `data`。

生成的数据：

- `docs.jsonl`：token 和词性分开后的文章 list。
- `inv_idx_roaring.pkl`：id 到 postings list 的映射，以 Roaring Bitmap 方法存储。
- `token_freq`：token 到词频的映射。
- `token_to_id`：token 到 id 的映射。
- `vocab.txt`：词汇表。
- `id_to_date.txt`：id 到日期的映射。

然后执行在 `sbert` 下执行 `python embedder.py` 生成每个文章的 top 100 个最相似文章，存到 `data` 和 `data/similar_docs`。

- `text_docs.jsonl`：每个文章内容转换成连续文字。
- `embeddings.pkl`：每个文章的向量。
- `similar_docs/*.pkl`：每个文章的 top 100 最相似文章的 index。

### 2 后端

在 `src/backend` 下执行 `flask run`，但是注意虽然可以跑起来，但是查询时必须要启动 Elasticsearch 才能获得结果。

### 3 前端

打开 `src/frontend/index.html` 即可，但是注意需要联网才能成功渲染页面。
