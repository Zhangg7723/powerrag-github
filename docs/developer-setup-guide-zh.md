# PowerRAG 源码部署开发者手册

> 本手册记录了基于源码从零部署 PowerRAG 的完整流程，数据库使用 SeekDB (OceanBase) Docker 容器，适用于本地开发环境。

---

## 目录

- [快速启动](#快速启动)
- [1. 环境要求](#1-环境要求)
- [2. 数据库部署（SeekDB）](#2-数据库部署seekdb)
- [3. 后端部署](#3-后端部署)
- [4. 前端部署](#4-前端部署)
- [5. 常见问题与解决方案](#5-常见问题与解决方案)

---

## 快速启动

以下是完整部署的快速参考命令：

```bash
# 1. 启动 SeekDB 数据库
docker run -d --name powerrag-seekdb \
  -p 2881:2881 \
  -e ROOT_PASSWORD=powerrag \
  -e INIT_SCRIPTS_PATH=/root/boot/init.d \
  -v $(pwd)/docker/oceanbase/init.d:/root/boot/init.d \
  oceanbase/seekdb:1.0.0.0-100000262025111218

# 2. 等待数据库就绪 & 创建数据库
sleep 60
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e \
  "CREATE DATABASE IF NOT EXISTS powerrag; CREATE DATABASE IF NOT EXISTS powerrag_doc;"

# 3. 安装 Python 依赖
uv sync --python 3.12 --all-extras

# 4. 下载模型与 NLP 资源
docker pull infiniflow/ragflow_deps:latest
bash set_backend_deps.sh

# 5. 启动后端
source .venv/bin/activate
export PYTHONPATH=$(pwd)
bash docker/launch_backend_service.sh &

# 6. 安装前端依赖
cd web
npm install

# 7. 启动前端
npm run dev &

# 8. 访问
# 前端：http://localhost:9222
# API：http://localhost:9380
```

---

## 1. 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| **操作系统** | Linux (x86_64) | 已在 AlmaLinux 8 (kernel 5.10) 上验证 |
| **Python** | ≥ 3.12, < 3.15 | 推荐 3.12.x |
| **uv** | ≥ 0.9.x | Python 包管理器 |
| **Node.js** | ≥ 22.x | 前端构建 |
| **npm** | ≥ 10.x | 前端包管理 |
| **Docker** | ≥ 20.x | 运行 SeekDB 数据库 |
| **磁盘空间** | ≥ 50GB | 数据库 + 模型文件 + 依赖 |
| **内存** | ≥ 16GB | SeekDB 推荐 10GB+，应用服务 4GB+ |

---

## 2. 数据库部署（SeekDB）

### 2.1 启动 SeekDB 容器

```bash
docker run -d \
  --name powerrag-seekdb \
  -p 2881:2881 \
  -e ROOT_PASSWORD=powerrag \
  -e INIT_SCRIPTS_PATH=/root/boot/init.d \
  -v $(pwd)/docker/oceanbase/init.d:/root/boot/init.d \
  oceanbase/seekdb:1.0.0.0-100000262025111218
```

> **说明**：
> - `ROOT_PASSWORD=powerrag`：设置数据库 root 密码，需与 `conf/service_conf.yaml` 中的配置保持一致
> - 初始化脚本 `docker/oceanbase/init.d/vec_memory.sql` 会执行 `ALTER SYSTEM SET ob_vector_memory_limit_percentage = 30;`，为向量搜索分配内存
> - 端口 `2881` 是 OceanBase 的 MySQL 协议端口

### 2.2 等待数据库就绪

SeekDB 启动需要约 30-60 秒。验证方法：

```bash
# 检查容器健康状态
docker ps --filter name=powerrag-seekdb --format 'table {{.Names}}\t{{.Status}}'

# 测试连接
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e "SELECT 1;"
```

### 2.3 创建数据库

```bash
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e "
  CREATE DATABASE IF NOT EXISTS powerrag;
  CREATE DATABASE IF NOT EXISTS powerrag_doc;
"
```

---

## 3. 后端部署

### 3.1 Python 依赖安装

```bash
cd /path/to/powerrag
uv sync --python 3.12 --all-extras
```

> **预计耗时**：首次安装约 10-20 分钟（取决于网络速度）。
>
> 项目已在 `pyproject.toml` 中配置了清华 PyPI 镜像源，国内网络可直接使用。

### 3.2 模型与 NLP 资源下载

PowerRAG 依赖多个预训练模型和 NLP 数据集。推荐使用预构建的 Docker 镜像快速获取：

```bash
# 先拉取依赖镜像
docker pull infiniflow/ragflow_deps:latest

# 执行依赖复制脚本
bash set_backend_deps.sh
```

该脚本会从 `infiniflow/ragflow_deps:latest` 镜像中复制以下资源：

| 资源 | 目标路径 | 用途 |
|------|---------|------|
| HuggingFace 深度文档模型 | `rag/res/deepdoc/` | 文档布局分析 |
| XGBoost 文本拼接模型 | `rag/res/deepdoc/` | 文本段落合并 |
| BAAI/bge-large-zh-v1.5 | `~/.ragflow/` | 中文向量嵌入 |
| BCE Embedding | `~/.ragflow/` | 向量嵌入 |
| NLTK 数据 | `nltk_data/` | 自然语言处理 |
| Tika Server | `tika-server-standard-3.2.3.jar` | 文档解析 |
| tiktoken 编码 | `9b5ad71b2ce5302211f9c61530b329a4922fc6a4` | Token 计算 |

### 3.3 启动后端服务

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)

# 使用启动脚本（同时启动 API Server、Task Executor 和 Data Sync 服务）
bash docker/launch_backend_service.sh
```

启动成功后，API Server 默认监听 `http://0.0.0.0:9380`。

#### 验证后端服务

```bash
curl -s http://localhost:9380/v1/system/healthz
# 预期返回：健康检查通过的 JSON 响应
```

#### 后端启动日志说明

正常启动时可能看到以下警告，属于预期行为：

| 日志信息 | 说明 |
|---------|------|
| `term.freq is not supported` | OceanBase 的全文索引不支持词频特性，不影响功能 |
| `Realtime synonym is disabled, since no redis connection` | 未配置 Redis，同义词实时更新功能不可用 |
| `pthread_setaffinity_np failed` | ONNX Runtime 线程亲和性设置失败，无影响 |

---

## 4. 前端部署

### 4.1 安装依赖

```bash
cd web
npm install
```

> **注意**：安装过程中会自动运行 Tailwind CSS 插件修复脚本（通过 `postinstall` 钩子），修复 UmiJS Tailwind 插件的已知问题。如果遇到 Tailwind CSS 生成失败，可手动运行：
> ```bash
> node scripts/fix-tailwindcss-plugin.js
> ```

### 4.2 启动前端开发服务器

```bash
cd web
npm run dev
```

前端开发服务器默认运行在 `http://localhost:9222`（通过 proxy 转发 API 请求到后端 9380 端口）。

---

## 5. 常见问题与解决方案

### Q1: `download_deps.py` 下载超时

**原因**：无法直接访问外部 URL（Maven、HuggingFace 等）

**解决**：使用 `set_backend_deps.sh` 从 Docker 镜像复制依赖：

```bash
docker pull infiniflow/ragflow_deps:latest
bash set_backend_deps.sh
```

---

### Q2: 连接 SeekDB 报 `Access denied`

**原因**：密码不匹配或容器未完全启动

**解决**：
1. 确认容器状态：`docker ps --filter name=powerrag-seekdb`
2. 确认密码与启动参数一致：`ROOT_PASSWORD=powerrag`
3. 等待容器 healthcheck 通过后再连接

---

### Q3: 后端启动报 `peewee.OperationalError: (1049, "Unknown database 'powerrag'")`

**原因**：数据库尚未创建

**解决**：

```bash
mysql -h127.0.0.1 -P2881 -uroot -ppowerrag -e "
  CREATE DATABASE IF NOT EXISTS powerrag;
  CREATE DATABASE IF NOT EXISTS powerrag_doc;
"
```

---

### Q4: ONNX Runtime 报 `pthread_setaffinity_np failed`

**原因**：某些容器化环境或受限 Linux 环境不支持线程亲和性设置

**解决**：此警告不影响功能，可忽略。
