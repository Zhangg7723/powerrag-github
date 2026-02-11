# PowerRAG SDK

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

PowerRAG SDK 是一个功能强大的 Python SDK，为 PowerRAG API 提供了简单易用的接口，支持知识库管理、文档处理、Markdown 解析、文本切片、信息抽取、RAPTOR 构建、知识图谱和检索等功能。

## 特性

- 🚀 **简单易用**: 面向对象的 API 设计，直观的方法调用
- 📚 **完整功能**: 支持 PowerRAG 所有核心功能模块，包括文档上传/解析/切片/提取/Raptor构建/知识库graph构建
- 🔄 **异步支持**: 支持异步任务的状态查询和轮询等待
- 📦 **批量操作**: 支持批量上传、删除、抽取等操作
- 📝 **Markdown 解析**: 支持文档解析为 Markdown 格式（同步/异步）

## 安装

### 使用 pip

```bash
pip install powerrag-sdk
```

### 依赖要求

- Python 3.10+
- requests >= 2.28.0
- typing-extensions (Python < 3.11)

### 验证安装

```python
from powerrag.sdk import PowerRAGClient

print(f"PowerRAG SDK installed successfully!")
```

## 快速开始

### 初始化客户端

```python
from powerrag.sdk import PowerRAGClient

# 创建客户端
client = PowerRAGClient(
    api_key="your-api-key",
    base_url="http://localhost:9380"
)
```

### 创建知识库

```python
# 创建知识库
kb = client.knowledge_base.create(
    name="my_knowledge_base",
    description="My first knowledge base",
    chunk_method="naive"
)
print(f"Knowledge Base ID: {kb['id']}")
```

### 上传文档

```python
# 上传单个文档
docs = client.document.upload(kb['id'], "document.pdf")

# 上传多个文档
docs = client.document.upload(kb['id'], ["doc1.pdf", "doc2.pdf", "doc3.pdf"])
```

### 解析文档为切片

```python
# 异步解析文档为切片
task_id = client.document.parse_to_chunk(
    kb['id'], 
    [docs[0]['id']], 
    wait=False
)

# 同步解析并等待完成
results = client.document.parse_to_chunk(
    kb['id'], 
    [docs[0]['id']], 
    wait=True,
    delete_existing=False
)
```

### 解析文档为 Markdown

```python
# 同步解析为 Markdown（不切分）
result = client.document.parse_to_md(
    doc_id=docs[0]['id'],
    config={
        "layout_recognize": "mineru",  # 或 "dots_ocr"
        "enable_ocr": False,
        "enable_formula": False,
        "enable_table": True
    }
)
# 默认返回完整内容，pages 包含 1 个元素，page_num=-1
print(f"Content: {result['pages'][0]['content'][:200]}")

# 按页解析
result = client.document.parse_to_md(
    doc_id=docs[0]['id'],
    config={"return_pages": True, "layout_recognize": "mineru"}
)
for page in result['pages']:
    print(f"Page {page['page_num']}: {page['content'][:100]}")

# 异步解析为 Markdown
task_id = client.document.parse_to_md_async(
    doc_id=docs[0]['id'],
    config={"layout_recognize": "mineru"}
)

# 查询异步任务状态
status = client.document.get_parse_to_md_status(task_id)
print(f"Status: {status['status']}")

# 等待任务完成
result = client.document.wait_for_parse_to_md(task_id, timeout=300)

# 直接上传文件并解析为 Markdown（无需知识库）
result = client.document.parse_to_md_upload(
    "document.pdf",
    config={"layout_recognize": "mineru"}
)
# 访问返回结果（统一 pages 格式）
print(result['pages'][0]['content'])  # Markdown 内容

# 按页上传解析
result = client.document.parse_to_md_upload(
    "document.pdf",
    config={"return_pages": True, "layout_recognize": "mineru"}
)
for page in result['pages']:
    print(f"Page {page['page_num']}: {page['content'][:100]}")

# 从 URL 下载并解析（直接调用 API）
import requests
import json

response = requests.post(
    f"{client.api_url}/powerrag/parse_to_md/upload",
    headers={"Authorization": f"Bearer {client.api_key}"},
    data={
        "file_url": "https://example.com/document.pdf",
        "config": json.dumps({"layout_recognize": "mineru"})
    }
)
result = response.json()
# 访问返回结果（统一 pages 格式）
print(result['data']['pages'][0]['content'])  # Markdown 内容

# 使用二进制数据解析（支持无扩展名文件）
with open("document.pdf", "rb") as f:
    binary_data = f.read()

result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document.pdf",  # 有扩展名时自动识别
    config={"layout_recognize": "mineru"}
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容

# 对于无扩展名的文件，使用 input_type='auto' 自动识别
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document_no_extension",  # 无扩展名
    # input_type='auto' 是默认值，会自动从二进制内容检测文件类型
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容

# 或显式指定文件类型（使用具体扩展名）
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document",
    input_type="pdf"  # 具体扩展名: 'pdf', 'docx', 'html', 'jpg' 等
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容
```

### 检索

```python
# 执行检索
result = client.retrieval.search(
    kb_ids=[kb['id']],
    question="什么是 PowerRAG?",
    page_size=10,
    similarity_threshold=0.2
)

# 打印结果
for chunk in result['chunks']:
    print(f"Content: {chunk['content']}")
    print(f"Score: {chunk['similarity']}")
    print(f"Document: {chunk['document_name']}")
```

## 核心功能亮点

### 文档解析为 Markdown

PowerRAG SDK 提供了强大的文档解析为 Markdown 的功能，支持多种文档格式：

**支持的格式：**
- PDF (.pdf)
- Office 文档 (.doc, .docx, .ppt, .pptx)
- 图片 (.jpg, .png)
- HTML (.html, .htm)

**四种使用方式：**

1. **同步解析**（适合小文档）：
```python
result = client.document.parse_to_md(doc_id, config={...})
# 访问 Markdown 内容
print(result['pages'][0]['content'])

# 按页解析
result = client.document.parse_to_md(doc_id, config={"return_pages": True})
for page in result['pages']:
    print(f"Page {page['page_num']}: {page['content'][:100]}")
```

2. **异步解析**（适合大文档）：
```python
task_id = client.document.parse_to_md_async(doc_id, config={...})
status = client.document.get_parse_to_md_status(task_id)
# 或等待完成
result = client.document.wait_for_parse_to_md(task_id, timeout=300)
```

3. **直接上传解析**（无需知识库）：
```python
# 上传本地文件
result = client.document.parse_to_md_upload("file.pdf", config={...})
print(result['pages'][0]['content'])  # Markdown 内容

# 或使用 file_url 参数从URL下载（通过 config 传入）
import requests
response = requests.post(
    "http://localhost:9390/api/v1/powerrag/parse_to_md/upload",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    data={
        "file_url": "https://example.com/document.pdf",
        "config": json.dumps({"layout_recognize": "mineru"})
    }
)
```

4. **二进制数据解析**（支持无扩展名文件）：
```python
with open("document.pdf", "rb") as f:
    binary_data = f.read()

# 自动识别文件类型（默认）
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document_no_extension"  # 无扩展名也可以
)
# 访问返回结果（统一 pages 格式）
print(result['pages'][0]['content'])  # Markdown 内容

# 或显式指定类型
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document",
    input_type="pdf"  # 具体扩展名: 'pdf', 'docx', 'html', 'jpg' 等
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容
```

**配置选项：**
- `return_pages`: 是否按页返回（默认 `false`），设为 `true` 时每页独立返回
- `layout_recognize`: 布局识别引擎 (`"mineru"` 或 `"dots_ocr"`)
- `enable_ocr`: 是否启用 OCR
- `enable_formula`: 是否识别公式
- `enable_table`: 是否识别表格
- `from_page`/`to_page`: PDF 页面范围
- `input_type`: 文件类型识别模式（默认: `'auto'`）
  - `'auto'`: 优先使用文件扩展名，无扩展名时自动检测（推荐）
  - 具体文件扩展名: `'pdf'`, `'docx'`, `'doc'`, `'xlsx'`, `'xls'`, `'pptx'`, `'ppt'`, `'html'`, `'htm'`, `'jpg'`, `'jpeg'`, `'png'` - 显式指定文件扩展名

**统一返回格式：**
- 所有 parse_to_md 接口统一返回 `pages` 数组 + `total_pages` + `images` + `total_images`
- `return_pages=false`（默认）: `pages` 包含 1 个元素，`page_num=-1`，`content` 为完整文档内容
- `return_pages=true`: `pages` 包含每页独立的 Markdown，`page_num` 从 1 开始
- `images`: 文档中提取的图片（key 为图片名，value 为 base64 编码内容）
- `total_images`: 提取的图片总数

### 结构化信息抽取

支持使用 LangExtract 进行结构化信息抽取：

```python
task = client.extraction.struct_extract(
    text_or_documents="...",
    prompt_description="Extract person information",
    examples=[...],
    temperature=0.0
)
status = client.extraction.get_struct_extract_status(task['task_id'])
```

### 文本切片

无需上传文档即可对文本进行切片：

```python
result = client.chunk.split_text(
    text="# Title\n\nContent...",
    parser_id="title",
    config={"chunk_token_num": 512}
)
```

## 核心模块

PowerRAG SDK 包含以下 7 个核心模块：

### 1. 知识库管理 (Knowledge Base)

管理知识库的创建、查询、更新和删除。

```python
# 创建知识库
kb = client.knowledge_base.create(
    name="test_kb",
    description="Test knowledge base",
    embedding_model="BAAI/bge-small-en-v1.5@Builtin",
    permission="me",
    chunk_method="naive"
)

# 获取知识库
kb_info = client.knowledge_base.get(kb['id'])

# 列出知识库
kbs, total = client.knowledge_base.list(
    name="test",
    page=1,
    page_size=10
)

# 更新知识库
updated_kb = client.knowledge_base.update(
    kb['id'],
    description="Updated description",
    pagerank=True
)

# 删除知识库
client.knowledge_base.delete([kb['id']])
```

### 2. 文档管理 (Document)

处理文档的上传、列表、查询、更新、删除、下载和解析。

```python
# 上传文档
docs = client.document.upload(kb_id, ["file1.pdf", "file2.docx"])

# 从URL上传文档
success = client.document.upload_from_url(
    kb_id,
    url="https://example.com/doc.pdf",
    name="document.pdf"
)

# 列出文档
docs, total = client.document.list(
    kb_id,
    name="report",
    page=1,
    page_size=20,
    keywords="机器学习",  # 关键词搜索
    suffix=["pdf", "docx"],  # 按后缀过滤
    run=["DONE", "FAIL"]  # 按状态过滤
)

# 获取文档详情
doc = client.document.get(kb_id, doc_id)

# 更新文档
updated_doc = client.document.update(
    kb_id,
    doc_id,
    name="new_name.pdf",
    meta_fields={"author": "John", "category": "AI"},
    enabled=True
)

# 快捷方法：重命名文档
client.document.rename(kb_id, doc_id, "renamed.pdf")

# 快捷方法：设置元数据
client.document.set_meta(kb_id, doc_id, {"version": "1.0"})

# 下载文档
# 下载为字节流
file_bytes = client.document.download(kb_id, doc_id)

# 下载到文件
saved_path = client.document.download(kb_id, doc_id, save_path="downloaded.pdf")

# 解析文档为切片（异步）
task_id = client.document.parse_to_chunk(kb_id, [doc_id], wait=False)

# 解析文档为切片（同步等待）
results = client.document.parse_to_chunk(
    kb_id, 
    [doc_id], 
    wait=True,
    delete_existing=False,  # 是否删除已有切片
    config={"max_token": 512}  # 自定义配置
)

# 解析文档为 Markdown（同步，默认整体解析）
result = client.document.parse_to_md(
    doc_id,
    config={
        "layout_recognize": "mineru",  # mineru 或 dots_ocr
        "enable_ocr": False,
        "enable_formula": False,
        "enable_table": True,
        "from_page": 0,  # PDF起始页
        "to_page": 100   # PDF结束页
    }
)
print(result['pages'][0]['content'])  # 完整 Markdown 内容

# 按页解析
result = client.document.parse_to_md(
    doc_id,
    config={"return_pages": True}
)
for page in result['pages']:
    print(f"Page {page['page_num']}: {page['content'][:100]}")

# 解析文档为 Markdown（异步）
task_id = client.document.parse_to_md_async(doc_id, config={...})

# 查询 parse_to_md 任务状态
status = client.document.get_parse_to_md_status(task_id)
if status["status"] == "success":
    print(status["result"]["pages"][0]["content"])  # 新格式
    print(status["result"]["markdown"])  # 兼容旧格式

# 等待 parse_to_md 任务完成
result = client.document.wait_for_parse_to_md(task_id, timeout=300)

# 上传并解析为 Markdown（无需知识库）
result = client.document.parse_to_md_upload("file.pdf", config={...})
# 访问返回结果（统一 pages 格式）
print(result['pages'][0]['content'])  # Markdown 内容

# 使用 file_url 参数从 URL 下载并解析（直接调用 API）
import requests
import json

response = requests.post(
    f"{client.api_url}/powerrag/parse_to_md/upload",
    headers={"Authorization": f"Bearer {client.api_key}"},
    data={
        "file_url": "https://example.com/document.pdf",
        "config": json.dumps({
            "layout_recognize": "mineru",
            "input_type": "auto"  # 可选，自动检测文件类型
        })
    }
)
result = response.json()
# 访问返回结果（统一 pages 格式）
print(result['data']['pages'][0]['content'])  # Markdown 内容

# 使用 file_url 并指定文件名
response = requests.post(
    f"{client.api_url}/powerrag/parse_to_md/upload",
    headers={"Authorization": f"Bearer {client.api_key}"},
    data={
        "file_url": "https://example.com/download?id=123",
        "config": json.dumps({
            "filename": "report.pdf",  # 自定义文件名
            "input_type": "pdf",
            "layout_recognize": "mineru"
        })
    }
)
result = response.json()
# 访问返回结果
print(result['data']['pages'][0]['content'])  # Markdown 内容

# 使用二进制数据解析为 Markdown
with open("document.pdf", "rb") as f:
    binary_data = f.read()

result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document.pdf",
    config={"layout_recognize": "mineru"},
    input_type="auto"  # 默认值，自动识别文件类型
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容

# 无扩展名文件解析（自动检测文件类型）
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document_no_extension",  # 无扩展名
    # input_type='auto' 会从二进制内容自动检测 PDF/Office/HTML 等
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容

# 显式指定文件类型（跳过自动检测）
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document",
    input_type="pdf"  # 强制作为 PDF 处理
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容

# 解析URL文档（同步等待）
doc = client.document.parse_url(
    kb_id,
    url="https://example.com/doc.pdf",
    name="web_doc.pdf",
    wait=True
)

# 取消解析任务
client.document.cancel_parse(kb_id, [doc_id])

# 删除文档
client.document.delete(kb_id, [doc_id])
```

### 3. 切片管理 (Chunk)

管理文档切片的查询、创建、更新、删除和文本切片。

```python
# 列出文档的切片
chunks, total, doc_info = client.chunk.list(
    kb_id,
    doc_id,
    keywords="机器学习",
    page=1,
    page_size=30
)

# 获取切片详情
chunk = client.chunk.get(kb_id, doc_id, chunk_id)

# 创建切片
chunk = client.chunk.create(
    kb_id,
    doc_id,
    content="This is a chunk content",
    important_keywords=["keyword1", "keyword2"],
    questions=["What is this about?"]
)

# 更新切片
updated_chunk = client.chunk.update(
    kb_id,
    doc_id,
    chunk_id,
    content="Updated content",
    important_keywords=["new_keyword"],
    questions=["Updated question?"],
    available=True,
    positions=[[0, 100]]
)

# 删除切片
client.chunk.delete(kb_id, doc_id, [chunk_id])

# 删除文档的所有切片
client.chunk.delete(kb_id, doc_id, None)

# 文本切片（无需上传文档）
result = client.chunk.split_text(
    text="# Title\n\nLong text to be chunked...",
    parser_id="title",  # 解析器ID
    config={"chunk_token_num": 512}  # 自定义配置
)
print(f"Total chunks: {result['total_chunks']}")
for chunk in result['chunks']:
    print(chunk['content'])
```

### 4. 信息抽取 (Extraction)

从文档或文本中抽取实体、关键词、摘要等信息。

```python
# 从文档抽取
result = client.extraction.extract_from_document(
    doc_id=doc_id,
    extractor_type="entity",  # entity, keyword, summary
    config={
        "entity_types": ["PERSON", "ORG", "LOC"],
        "use_regex": True,
        "use_llm": False
    }
)
print(result['entities'])

# 从文本抽取
result = client.extraction.extract_from_text(
    text="PowerRAG is an advanced RAG framework developed by OceanBase",
    extractor_type="entity",
    config={"entity_types": ["ORG", "PRODUCT"]}
)

# 抽取关键词
result = client.extraction.extract_from_document(
    doc_id=doc_id,
    extractor_type="keyword",
    config={
        "max_keywords": 20,
        "min_word_length": 3
    }
)

# 抽取摘要
result = client.extraction.extract_from_document(
    doc_id=doc_id,
    extractor_type="summary",
    config={
        "max_length": 200,
        "min_length": 50
    }
)

# 批量抽取
results = client.extraction.extract_batch(
    doc_ids=[doc_id1, doc_id2, doc_id3],
    extractor_type="keyword",
    config={"max_keywords": 15}
)
for result in results:
    if result['success']:
        print(f"Doc {result['doc_id']}: {result['data']}")

# 结构化抽取 (LangExtract)
task = client.extraction.struct_extract(
    text_or_documents="John Doe is 30 years old. His email is john@example.com",
    prompt_description="Extract person information including name, age, and email",
    examples=[
        {
            "text": "Jane Smith is 25 years old. Email: jane@example.com",
            "extractions": [
                {"name": "Jane Smith", "age": 25, "email": "jane@example.com"}
            ]
        }
    ],
    fetch_urls=False,
    max_char_buffer=1000,
    temperature=0.0,
    extraction_passes=1
)
print(f"Task ID: {task['task_id']}")

# 获取结构化抽取状态
status = client.extraction.get_struct_extract_status(task['task_id'])
print(f"Status: {status['status']}")
if status['status'] == 'completed':
    print(f"Result: {status['result']}")
```

### 5. RAPTOR

构建和管理 RAPTOR（Recursive Abstractive Processing for Tree-Organized Retrieval）。

**注意**: RAPTOR 的配置参数需要在创建或更新知识库时通过 `parser_config.raptor` 设置。

```python
# 创建知识库时配置 RAPTOR 参数
kb = client.knowledge_base.create(
    name="raptor_kb",
    chunk_method="naive",
    parser_config={
        "raptor": {
            "max_cluster": 64,
            "random_seed": 224,
            "llm_model": "deepseek-chat"
        }
    }
)

# 构建 RAPTOR（异步）
task = client.raptor.build(kb_id)
print(f"RAPTOR Task ID: {task['raptor_task_id']}")

# 获取 RAPTOR 构建状态
status = client.raptor.get_status(kb_id)
if status:
    print(f"Status: {status['status']}")
    print(f"Progress: {status['progress']}")
else:
    print("No RAPTOR task found")
```

### 6. 知识图谱 (Knowledge Graph)

构建和管理知识图谱。

**注意**: 知识图谱的配置参数需要在创建或更新知识库时通过 `parser_config.graphrag` 设置。

```python
# 创建知识库时配置知识图谱参数
kb = client.knowledge_base.create(
    name="kg_kb",
    chunk_method="naive",
    parser_config={
        "graphrag": {
            "entity_types": ["PERSON", "ORG", "LOC", "EVENT"],
            "llm_model": "deepseek-chat"
        }
    }
)

# 构建知识图谱（异步）
task = client.knowledge_graph.build(kb_id)
print(f"Knowledge Graph Task ID: {task['graphrag_task_id']}")

# 获取知识图谱数据
kg = client.knowledge_graph.get(kb_id)
print(f"Graph nodes: {len(kg['graph'].get('nodes', []))}")
print(f"Graph edges: {len(kg['graph'].get('edges', []))}")
print(f"Mind map: {kg['mind_map']}")

# 获取构建状态
status = client.knowledge_graph.get_status(kb_id)
if status:
    print(f"Status: {status['status']}")
    print(f"Progress: {status['progress']}")
else:
    print("No knowledge graph task found")
```

### 7. 检索 (Retrieval)

执行语义检索和混合检索。

```python
# 基本检索
result = client.retrieval.search(
    kb_ids=[kb_id],
    question="What is PowerRAG?",
    page=1,
    page_size=10
)

# 打印结果
print(f"Total results: {result['total']}")
for chunk in result['chunks']:
    print(f"Content: {chunk['content']}")
    print(f"Similarity: {chunk['similarity']}")
    print(f"Document: {chunk['document_name']}")

# 高级检索
result = client.retrieval.search(
    kb_ids=[kb_id1, kb_id2],
    question="机器学习的应用",
    document_ids=[doc_id],  # 限定文档范围
    page=1,
    page_size=30,
    similarity_threshold=0.3,  # 相似度阈值
    vector_similarity_weight=0.3,  # 向量相似度权重（混合检索）
    top_k=1024,  # 最大返回数量
    keyword=True,  # 启用关键词增强
    use_kg=True,  # 使用知识图谱检索
    rerank_id="bge-reranker-v2-m3",  # 重排序模型
    highlight=True,  # 高亮匹配内容
    cross_languages=["en", "zh"],  # 跨语言检索
    metadata_condition={"status": "published", "year": 2024}  # 元数据过滤
)

# 检索测试（与 search 功能相同，用于测试场景）
test_result = client.retrieval.test(
    kb_ids=[kb_id],
    question="测试查询",
    page=1,
    page_size=50,
    similarity_threshold=0.2,
    keyword=True,
    use_kg=False
)
```

## 完整示例

以下是一个完整的工作流程示例：

```python
from powerrag.sdk import PowerRAGClient
import time

# 初始化客户端
client = PowerRAGClient(
    api_key="your-api-key",
    base_url="http://localhost:9380"
)

# 1. 创建知识库
kb = client.knowledge_base.create(
    name="research_papers",
    description="Collection of AI research papers",
    chunk_method="naive"
)
print(f"Created knowledge base: {kb['id']}")

# 2. 上传文档
docs = client.document.upload(
    kb['id'],
    ["paper1.pdf", "paper2.pdf", "paper3.pdf"]
)
print(f"Uploaded {len(docs)} documents")

# 3. 解析文档为切片（同步等待）
doc_ids = [doc['id'] for doc in docs]
results = client.document.parse_to_chunk(kb['id'], doc_ids, wait=True)
print(f"Parsed {len(results)} documents")
for result in results:
    print(f"Doc {result['doc_id']}: {result['status']}, {result['chunk_count']} chunks")

# 4. 构建知识图谱（可选）
kg_task = client.knowledge_graph.build(kb['id'])
print(f"Building knowledge graph: {kg_task['graphrag_task_id']}")

# 等待知识图谱构建完成
while True:
    status = client.knowledge_graph.get_status(kb['id'])
    if not status:
        break
    print(f"KG status: {status['status']}, progress: {status.get('progress', 0)}")
    if status['status'] in ['DONE', 'FAIL']:
        break
    time.sleep(5)

# 5. 执行检索
result = client.retrieval.search(
    kb_ids=[kb['id']],
    question="What are the latest advances in transformer models?",
    page_size=5,
    similarity_threshold=0.2,
    use_kg=True,
    highlight=True
)

# 打印检索结果
print(f"\nFound {result['total']} results:")
for i, chunk in enumerate(result['chunks'], 1):
    print(f"\n{i}. Score: {chunk['similarity']:.3f}")
    print(f"   Content: {chunk['content'][:200]}...")
    print(f"   Document: {chunk['document_name']}")

# 6. 从文档抽取关键信息
for doc_id in doc_ids[:3]:  # 抽取前3个文档
    extraction = client.extraction.extract_from_document(
        doc_id=doc_id,
        extractor_type="keyword",
        config={"max_keywords": 10}
    )
    print(f"\nExtracted keywords from {doc_id}: {extraction.get('keywords', [])}")

# 7. 解析文档为 Markdown（可选）
md_result = client.document.parse_to_md(
    doc_id=doc_ids[0],
    config={"layout_recognize": "mineru"}
)
print(f"\nMarkdown content: {md_result['pages'][0]['content'][:200]}")
print(f"Total pages: {md_result['total_pages']}")

# 8. 清理（如需要）
# 删除特定文档
# client.document.delete(kb['id'], [doc_ids[0]])

# 删除整个知识库（包括所有文档）
# client.knowledge_base.delete([kb['id']])
```

## 环境配置

使用 SDK 前需要配置以下环境变量（可选）：

```bash
# PowerRAG 服务地址
export HOST_ADDRESS="http://127.0.0.1:9380"

# API 密钥
export POWERRAG_API_KEY="your-api-key"
```

或在代码中直接指定：

```python
client = PowerRAGClient(
    api_key="your-api-key",
    base_url="http://127.0.0.1:9380",
    version="v1"  # API 版本，默认为 v1
)
```

## 测试

SDK 包含完整的测试套件，覆盖所有功能模块。

### 运行所有测试

```bash
# 设置环境变量
export HOST_ADDRESS="http://127.0.0.1:9380"
export POWERRAG_API_KEY="your-api-key"

# 运行测试
pytest powerrag/sdk/tests/
```

### 运行特定模块测试

```bash
# 测试知识库模块
pytest powerrag/sdk/tests/test_knowledge_base.py

# 测试文档模块
pytest powerrag/sdk/tests/test_document.py

# 测试检索模块
pytest powerrag/sdk/tests/test_retrieval.py
```

更多测试说明请参考 [tests/README.md](tests/README.md)。

## 项目结构

```
powerrag/sdk/
├── __init__.py                      # SDK 入口，导出 PowerRAGClient
├── client.py                        # 主客户端类，提供 HTTP 请求方法
├── README.md                        # SDK 文档（本文件）
├── modules/                         # 功能模块
│   ├── knowledge_base.py            # 知识库数据模型 (TypedDict)
│   ├── knowledge_base_manager.py    # 知识库管理器
│   ├── document.py                  # 文档数据模型 (TypedDict)
│   ├── document_manager.py          # 文档管理器
│   ├── chunk.py                     # 切片数据模型 (TypedDict)
│   ├── chunk_manager.py             # 切片管理器
│   ├── extraction.py                # 抽取数据模型 (TypedDict)
│   ├── extraction_manager.py        # 抽取管理器
│   ├── raptor.py                    # RAPTOR 数据模型 (TypedDict)
│   ├── raptor_manager.py            # RAPTOR 管理器
│   ├── knowledge_graph.py           # 知识图谱数据模型 (TypedDict)
│   ├── knowledge_graph_manager.py   # 知识图谱管理器
│   ├── retrieval.py                 # 检索数据模型 (TypedDict)
│   └── retrieval_manager.py         # 检索管理器
└── tests/                           # 完整的测试套件
    ├── README.md                    # 测试文档
    ├── conftest.py                  # pytest 配置和 fixtures
    ├── pytest.ini                   # pytest 配置文件
    ├── test_knowledge_base.py       # 知识库测试
    ├── test_document.py             # 文档测试
    ├── test_chunk.py                # 切片测试
    ├── test_extraction.py           # 抽取测试
    ├── test_raptor.py               # RAPTOR 测试
    ├── test_knowledge_graph.py      # 知识图谱测试
    └── test_retrieval.py            # 检索测试
```

## API 参考

### PowerRAGClient

主客户端类，提供对所有功能模块的访问。

**初始化参数：**
- `api_key` (str): API 密钥，必填
- `base_url` (str): 服务地址，默认 `"http://localhost:9380"`
- `version` (str): API 版本，默认 `"v1"`

**属性：**
- `knowledge_base` (KnowledgeBaseManager): 知识库管理器
- `document` (DocumentManager): 文档管理器
- `chunk` (ChunkManager): 切片管理器
- `extraction` (ExtractionManager): 抽取管理器
- `raptor` (RAPTORManager): RAPTOR 管理器
- `knowledge_graph` (KnowledgeGraphManager): 知识图谱管理器
- `retrieval` (RetrievalManager): 检索管理器

**内部方法：**
- `post(url, json=None, files=None, data=None, stream=False)`: POST 请求
- `get(url, params=None, stream=False)`: GET 请求
- `put(url, json=None)`: PUT 请求
- `delete(url, json=None, params=None)`: DELETE 请求

### 数据模型

所有数据模型都使用 `TypedDict` 定义，提供完整的类型提示：

**知识库相关：**
- `KnowledgeBaseInfo`: 知识库信息

**文档相关：**
- `DocumentInfo`: 文档信息

**切片相关：**
- `ChunkInfo`: 切片信息

**抽取相关：**
- `ExtractionResult`: 抽取结果
- `StructExtractTaskInfo`: 结构化抽取任务信息

**RAPTOR 相关：**
- `RAPTORTaskInfo`: RAPTOR 任务信息

**知识图谱相关：**
- `KnowledgeGraphData`: 知识图谱数据
- `KnowledgeGraphTaskInfo`: 知识图谱任务信息

**检索相关：**
- `RetrievalResult`: 检索结果

## 最佳实践

### 1. 错误处理

SDK 会抛出异常，建议在生产环境中进行适当的错误处理：

```python
from requests.exceptions import RequestException, HTTPError

try:
    result = client.retrieval.search(
        kb_ids=[kb_id],
        question="test query"
    )
except RequestException as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

### 2. 异步任务处理

对于长时间运行的任务，建议使用异步方式：

```python
# 提交任务
task_id = client.document.parse_to_chunk(kb_id, doc_ids, wait=False)

# 轮询状态
import time
for doc_id in doc_ids:
    while True:
        doc = client.document.get(kb_id, doc_id)
        if doc['run'] in ['DONE', 'FAIL']:
            break
        time.sleep(2)
```

### 3. 批量操作

充分利用批量操作提高效率：

```python
# 批量上传
docs = client.document.upload(kb_id, ["doc1.pdf", "doc2.pdf", "doc3.pdf"])

# 批量解析
doc_ids = [doc['id'] for doc in docs]
results = client.document.parse_to_chunk(kb_id, doc_ids, wait=True)

# 批量抽取
results = client.extraction.extract_batch(doc_ids, extractor_type="keyword")
```

### 4. 知识库配置

在创建知识库时就配置好所需的参数：

```python
kb = client.knowledge_base.create(
    name="my_kb",
    chunk_method="naive",
    embedding_model="BAAI/bge-large-zh-v1.5@Builtin",
    parser_config={
        "chunk_token_num": 512,
        "raptor": {
            "max_cluster": 64,
            "llm_model": "deepseek-chat"
        },
        "graphrag": {
            "entity_types": ["PERSON", "ORG", "LOC"],
            "llm_model": "deepseek-chat"
        }
    }
)
```

### 5. 检索优化

根据场景调整检索参数：

```python
# 精确检索（高阈值）
result = client.retrieval.search(
    kb_ids=[kb_id],
    question="query",
    similarity_threshold=0.5,  # 更高的阈值
    page_size=10
)

# 召回优化（低阈值 + 大top_k + 重排序）
result = client.retrieval.search(
    kb_ids=[kb_id],
    question="query",
    similarity_threshold=0.1,  # 更低的阈值
    top_k=2048,  # 更大的候选集
    rerank_id="bge-reranker-v2-m3",  # 使用重排序
    keyword=True,  # 启用关键词
    use_kg=True  # 使用知识图谱
)
```

## 错误处理

SDK 会抛出以下类型的异常：

**常见异常：**
- `FileNotFoundError`: 文件不存在
- `Exception`: API 调用失败（包含错误消息）
- `TimeoutError`: 任务超时（仅在使用 `wait_for_*` 方法时）
- `RequestException`: 网络请求错误

**示例：**

```python
try:
    kb = client.knowledge_base.get("nonexistent-id")
except Exception as e:
    print(f"Error: {e}")
```

```python
from requests.exceptions import RequestException

try:
    result = client.retrieval.search(
        kb_ids=[kb_id],
        question="test query"
    )
except RequestException as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## 常见问题 (FAQ)

### Q: 如何处理大文档的解析？

A: 对于大文档，建议使用异步解析：
```python
# 使用异步解析
task_id = client.document.parse_to_md_async(doc_id)
result = client.document.wait_for_parse_to_md(task_id, timeout=600)
```

### Q: RAPTOR 和知识图谱的配置在哪里设置？

A: 需要在创建或更新知识库时通过 `parser_config` 设置：
```python
kb = client.knowledge_base.create(
    name="my_kb",
    parser_config={
        "raptor": {"max_cluster": 64},
        "graphrag": {"entity_types": ["PERSON", "ORG"]}
    }
)
```

### Q: 如何查看知识库的 RAPTOR 和知识图谱状态？

A: 使用对应的 `get_status` 方法：
```python
raptor_status = client.raptor.get_status(kb_id)
kg_status = client.knowledge_graph.get_status(kb_id)
```
返回 `None` 表示没有运行中的任务。

### Q: 如何实现混合检索？

A: 调整 `vector_similarity_weight` 参数和启用 `keyword`：
```python
result = client.retrieval.search(
    kb_ids=[kb_id],
    question="query",
    vector_similarity_weight=0.3,  # 向量权重
    keyword=True,  # 启用关键词
    use_kg=True  # 使用知识图谱
)
```

### Q: 支持哪些抽取类型？

A: 支持三种抽取类型：
- `entity`: 实体抽取（人名、地名、组织等）
- `keyword`: 关键词抽取
- `summary`: 摘要生成

还支持结构化抽取 (`struct_extract`)，可以自定义抽取模式。

### Q: 如何处理解析失败的文档？

A: 检查文档状态并根据错误信息处理：
```python
results = client.document.parse_to_chunk(kb_id, doc_ids, wait=True)
for result in results:
    if result['status'] == 'FAIL':
        print(f"Document {result['doc_id']} failed to parse")
        # 重新解析或删除
```

### Q: 如何解析无扩展名的文件？

A: 使用 `parse_to_md_binary` 方法并使用 `input_type='auto'`（默认值）：
```python
with open("document_no_extension", "rb") as f:
    binary_data = f.read()

# input_type='auto' 会自动从二进制内容检测文件类型
result = client.document.parse_to_md_binary(
    file_binary=binary_data,
    filename="document_no_extension"
    # input_type='auto' 是默认值，可以省略
)
# 访问返回结果
print(result['pages'][0]['content'])  # Markdown 内容
```

支持的 `input_type` 值：
- `'auto'` (默认): 优先使用文件扩展名，无扩展名或不支持时从二进制内容自动检测
- 具体文件扩展名: `'pdf'`, `'docx'`, `'doc'`, `'xlsx'`, `'xls'`, `'pptx'`, `'ppt'`, `'html'`, `'htm'`, `'jpg'`, `'jpeg'`, `'png'` - 显式指定文件扩展名

### Q: 如何从URL直接解析文件？

A: 在 `/parse_to_md/upload` API 请求中使用 `file_url` 参数，服务器会自动下载并解析：

**方式 1：基本用法**
```python
import requests
import json

# 使用 file_url 参数
response = requests.post(
    "http://localhost:9390/api/v1/powerrag/parse_to_md/upload",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    data={
        "file_url": "https://example.com/document.pdf",
        "config": json.dumps({
            "layout_recognize": "mineru",
            "input_type": "auto"  # 可选，默认为 'auto'
        })
    }
)
result = response.json()
print(result['data']['pages'][0]['content'])
```

**方式 2：指定文件名（适用于无扩展名URL）**
```python
response = requests.post(
    "http://localhost:9390/api/v1/powerrag/parse_to_md/upload",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    data={
        "file_url": "https://api.example.com/download?id=123",
        "config": json.dumps({
            "filename": "report.pdf",  # 覆盖文件名
            "input_type": "pdf",  # 显式指定文件扩展名
            "layout_recognize": "mineru",
            "enable_table": True
        })
    }
)
```

**方式 3：与 SDK 客户端结合使用**
```python
from powerrag.sdk import PowerRAGClient
import requests
import json

client = PowerRAGClient(api_key="your-api-key", base_url="http://localhost:9390")

# 使用客户端的 api_url 和认证信息
response = requests.post(
    f"{client.api_url}/powerrag/parse_to_md/upload",
    headers={"Authorization": f"Bearer {client.api_key}"},
    data={
        "file_url": "https://example.com/document.pdf",
        "config": json.dumps({"layout_recognize": "mineru"})
    }
)
result = response.json()
# 访问返回结果（统一 pages 格式）
print(result['data']['pages'][0]['content'])  # Markdown 内容
```

**配置参数说明：**
- `file_url` (str): 文件的 URL 地址（与 `file` 参数二选一）
- `config.filename` (str): 自定义文件名（可选，不提供则从 URL 提取）
- `config.input_type` (str): 文件类型检测模式
  - `'auto'` (默认): 优先使用扩展名，无扩展名时自动检测
  - 具体文件扩展名: `'pdf'`, `'docx'`, `'doc'`, `'xlsx'`, `'xls'`, `'pptx'`, `'ppt'`, `'html'`, `'htm'`, `'jpg'`, `'jpeg'`, `'png'` - 显式指定文件扩展名
- `config.layout_recognize` (str): 布局识别引擎（`'mineru'` 或 `'dots_ocr'`）
- 其他解析配置参数同 `parse_to_md` 方法

**注意事项：**
- ✅ URL 必须可公开访问，不支持需要认证的 URL
- ✅ 下载超时时间为 60 秒
- ✅ 支持所有文件格式（PDF, Office, HTML, 图片）
- ✅ 自动从 URL 路径提取文件名，或使用 `config.filename` 覆盖
- ❌ 不能同时提供 `file` 和 `file_url` 参数
- ❌ 必须提供 `file` 或 `file_url` 其中之一

### Q: SDK 是否支持流式返回？

A: 当前版本主要支持标准 REST API 调用。对于下载等操作，SDK 内部使用了流式传输。

### Q: 如何设置请求超时？

A: 当前 SDK 使用 `requests` 库的默认超时。如需自定义，可以在调用前设置：
```python
import requests
requests.adapters.DEFAULT_RETRIES = 5
```

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

**贡献指南：**
- 遵循 PEP 8 代码规范
- 添加适当的类型注解
- 为新功能添加测试用例
- 更新相关文档

## 许可证

Copyright 2025 The OceanBase Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## 链接

- [PowerRAG 项目主页](https://github.com/oceanbase/powerrag)
- [API 文档](https://github.com/oceanbase/powerrag/docs)
- [问题反馈](https://github.com/oceanbase/powerrag/issues)
- [更新日志](https://github.com/oceanbase/powerrag/CHANGELOG.md)

## 支持

### 获取帮助

如有问题或建议，请：

1. 📖 查看 [完整文档](https://github.com/oceanbase/powerrag/docs)
2. 🔍 搜索 [已有问题](https://github.com/oceanbase/powerrag/issues)
3. 💬 创建 [新问题](https://github.com/oceanbase/powerrag/issues/new)
4. 📧 联系 OceanBase 团队

### 社区

- GitHub: [oceanbase/powerrag](https://github.com/oceanbase/powerrag)
- 文档: [PowerRAG Documentation](https://github.com/oceanbase/powerrag/docs)
- 问题跟踪: [GitHub Issues](https://github.com/oceanbase/powerrag/issues)

### 反馈

我们非常重视您的反馈！如果您：
- 发现了 bug
- 有功能建议
- 需要帮助
- 想要贡献代码

请通过 GitHub Issues 联系我们。

---

**Made with ❤️ by OceanBase Team**


