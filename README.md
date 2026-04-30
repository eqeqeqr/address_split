# 地址拆分系统

这是一个面向中文地址解析与拆分的前后端项目。后端基于 FastAPI 提供地址拆分、Excel 上传解析、拆分记录、场景规则、Redis 环境配置和任务进度接口；前端基于 Vue 3 + TypeScript + Vite 提供可视化操作界面。

## 功能介绍

- 地址拆分：支持手动输入地址和上传 Excel 文件进行批量拆分。
- 多种输出模式：支持 8 级地址、11 级地址和原始模型字段输出。
- 自定义场景：支持新增、编辑、删除和恢复默认场景规则。
- Excel 预检查：上传前可识别 Excel 列信息、地址列和数据量。
- 任务进度：支持拆分任务进度展示、WebSocket 进度推送和任务取消。
- 记录管理：支持查看拆分记录、分页查看拆分结果、下载结果文件和删除记录。
- 环境配置：支持 Redis 本地/远程连接配置和连接测试。

## 项目结构

```text
address_project/
  address_back/      # FastAPI 后端服务
  address_web/       # Vue 3 + Vite 前端应用
  README.md          # 项目说明文档
```

说明：`excel/`、`pdf/`、`原型设计/`、运行时上传文件、拆分结果、数据库、虚拟环境和前端依赖目录已加入 `.gitignore`，不会提交到 Git。

## 环境要求

- Python 3.11 或更高版本
- uv，推荐用于安装和运行后端依赖
- Node.js 18 或更高版本
- npm
- Redis，可选；默认配置为 `127.0.0.1:6379/0`
- Git LFS，用于拉取仓库中的大模型文件

## 拉取代码

```bash
git clone git@github.com:eqeqeqr/address_split.git
cd address_split
git lfs pull
```

如果没有安装 Git LFS，请先安装并启用：

```bash
git lfs install
git lfs pull
```

## 后端安装与运行

进入后端目录：

```bash
cd address_back
```

安装依赖：

```bash
uv sync
```

启动后端服务：

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端默认地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 前端安装与运行

打开新的终端，进入前端目录：

```bash
cd address_web
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run dev
```

前端默认通过下面的地址访问后端：

```text
http://127.0.0.1:8000/api
```

如需修改后端接口地址，可在 `address_web/.env.local` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## 常用命令

后端开发运行：

```bash
cd address_back
uv run uvicorn app.main:app --reload --port 8000
```

前端开发运行：

```bash
cd address_web
npm run dev
```

前端生产构建：

```bash
cd address_web
npm run build
```

前端本地预览构建结果：

```bash
cd address_web
npm run preview
```

## 数据与模型说明

- 后端运行数据默认写入 `address_back/data/`。
- 上传文件位于 `address_back/data/uploads/`。
- 拆分结果位于 `address_back/data/results/`。
- SQLite 数据库位于 `address_back/data/address.db`。
- 地址解析模型文件位于 `address_back/iic/`，仓库中通过 Git LFS 管理。

## Redis 配置

系统默认使用本地 Redis：

```text
redis://127.0.0.1:6379/0
```

也可以在前端“环境配置”页面修改 Redis 连接参数并测试连接。若本地没有 Redis，请先安装并启动 Redis，或在页面中配置可用的远程 Redis。

## 基本使用流程

1. 启动后端服务。
2. 启动前端开发服务。
3. 在浏览器打开前端页面。
4. 上传 Excel 或手动输入地址。
5. 选择列模式、场景字段和拆分参数。
6. 执行拆分并查看进度。
7. 在拆分记录中查看详情或下载结果。
