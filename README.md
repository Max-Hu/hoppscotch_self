# Hoppscotch 通用 Docker Compose 部署

将整个目录复制到另一台电脑。只需要 Docker 和 Docker Compose V2，不需要安装 Node.js、PostgreSQL 或桌面 API 客户端。Windows/macOS 可使用 Docker Desktop，Windows 需要 Linux containers 模式。镜像提供 Linux amd64 和 arm64 版本；本包已在当前 Windows + Docker Desktop 的 amd64 环境实测启动。

默认仅供安装它的那台电脑访问。浏览器、管理员界面、数据库、本地登录邮件和请求代理均在本机。固定 Hoppscotch 2026.10.0 及各镜像摘要，另一台电脑会按架构自动拉取相应镜像；首次下载镜像需要联网。ARM64 已核对镜像清单，未在 ARM64 硬件上实测。

## 1. 首次启动

在终端中进入解压后的本目录，执行以下命令（PowerShell、Linux shell、macOS 终端相同）：

```sh
docker compose run --rm init
docker compose up -d
docker compose ps -a
```

第一条命令通过临时 Node.js 容器创建 `.env`，自动生成数据库密码、加密密钥、会话密钥和本地代理令牌。无需手动复制 `.env.example`，也无需本机安装 Node.js。再次执行会校验并保留已有 `.env`，不会更换密钥。Linux 上可能生成归当前容器用户（root）所有的 `.env`，需要编辑时使用 sudo。

`migrate` 是一次性数据库初始化任务，状态 `Exited (0)` 表示成功。其余四个服务应处于运行状态，数据库和 Hoppscotch 会有健康检查。

| 功能 | 默认地址 |
| --- | --- |
| API 调试网页 | http://localhost:18080/ |
| 管理后台及首次配置 | http://localhost:18080/admin/ |
| 本地登录邮件收件箱 | http://localhost:8025/ |
| 本地请求代理 | http://localhost:9159/ |

### 首次配置与登录

1. 打开管理后台。如果显示 onboarding，点击 Start Onboarding，选择 SMTP。
2. SMTP URL 填写 `smtp://mailpit:1025`，Mailer From Address 填写 `noreply@hoppscotch.local`，保存并等待服务重启。
3. 进入管理后台登录，填写一个本地试用地址，例如 `admin@example.test`。
4. 打开本地邮件收件箱，按邮件提示完成验证码或登录链接验证。邮件只保存在本地 Mailpit，不会发送给真实邮箱。
5. 第一个登录管理后台的用户成为管理员。API 网页不登录也能先试用；登录后可使用服务器端账户功能。

## 2. 导入 Insomnia 与发送请求

在 API 网页的集合侧栏点击 Import，选择 Insomnia 并上传导出的 JSON 文件。脚本、测试和高级认证需另外检查；新版 v5 YAML 是否支持需用实际文件验证。

在 Settings → Interceptor 选择 **Proxy**，确认 Proxy URL 为 `http://localhost:9159`（或修改后的代理端口）。代理令牌由 Compose 注入，无需手动填写，也无需浏览器扩展。

可以用下面的地址发送 GET 测试请求，预期返回 `200` 和 `Success`：

```text
http://host.docker.internal:18080/backend/ping
```

代理在容器内运行，访问安装电脑上的接口时，将接口地址中的 `localhost` 改为 `host.docker.internal`。Linux 下，本机接口还需监听容器可达的宿主机接口；仅监听 `127.0.0.1` 的接口通常不能经容器代理访问。如果接口本身允许跨域，也可切换到 Browser 直接发送。

## 3. 修改端口

初始化后编辑 `.env` 中的三个端口，然后重新运行 `docker compose up -d`：

```dotenv
APP_PORT=18080
MAILPIT_PORT=8025
PROXY_PORT=9159
```

三个端口应不同。如果 Windows 报端口访问权限错误或已被占用，可换成 `28080`、`28025`、`29159`。网页和后端 URL 会随 APP_PORT 自动调整；页面中如有已保存的代理 URL，需同步修改。端口修改后必须通过新的 localhost 地址访问。

## 4. 日常管理

```sh
docker compose up -d
docker compose stop
docker compose ps -a
docker compose logs --tail 100 hoppscotch
docker compose logs --tail 50 migrate
```

`stop` 保留数据；再次执行 `up -d` 即可启动。Docker 启动后，未被手动停止的服务会自动恢复。数据存放在当前 Compose 项目的 Docker 命名卷中，修改项目名会切换到新的数据卷。

## 5. 在新电脑重新安装，或迁移现有数据

**重新安装一个空实例：** 复制此目录或解压部署包，按首次启动步骤操作。部署包不含本机 `.env`、账户、请求集合或数据库。

**迁移服务器端数据：** 除本目录外，必须携带原部署的 `.env` 和数据库备份，尤其要保留 `DATA_ENCRYPTION_KEY`，否则无法解密数据库中已有的配置。原部署和本包都使用 `db` 服务名、`hoppscotch` 数据库用户和数据库名，可用以下步骤迁移。

在旧电脑的部署目录运行（当前安装目录为 `hoppscotch-local`）：

```sh
docker compose exec -T db pg_dump -U hoppscotch -d hoppscotch -Fc -f /tmp/hoppscotch.dump
docker compose cp db:/tmp/hoppscotch.dump ./hoppscotch.dump
```

将旧部署的 `.env` 和 `hoppscotch.dump` 放到新电脑的本目录。旧 `.env` 如果没有端口变量，就会使用本包的默认端口；不需要重新生成密钥。先启动一个空数据库，再恢复：

```sh
docker compose up -d --wait db
docker compose cp ./hoppscotch.dump db:/tmp/hoppscotch.dump
docker compose exec -T db pg_restore --exit-on-error --no-owner --no-acl -U hoppscotch -d hoppscotch /tmp/hoppscotch.dump
docker compose up -d
```

以上恢复命令仅用于新建的空数据库。如果已经在新电脑完成了首次启动，应另用一个新的 Compose 项目名和未占用端口进行恢复，避免与已有表冲突。备份与原 `.env` 含敏感信息，请私下传输保存；不要提交到 Git 或公开分享。

**浏览器本地数据：** 未登录时保存的集合、历史和设置可能只在旧浏览器里。应另外在旧网页导出，再在新电脑导入，数据库备份不会带走浏览器本地存储。Mailpit 历史邮件也不包含在 PostgreSQL 备份中，新电脑可生成新的登录邮件。

## 文件与资料

- `compose.yaml`：服务、网络、端口和持久卷配置，无本机绝对路径。
- `.env.example`：端口及密钥模板，不含可用密钥。
- `init.mjs`：使用 Node.js 内置加密库生成密钥，默认拒绝覆盖已有配置。
- `.gitignore`：忽略实际密钥与数据库备份。
- 官方部署文档：https://docs.hoppscotch.io/documentation/self-host/community-edition/install-and-build

不要删除已有的 postgres_data 数据卷。此包按本机使用配置，Mailpit 是本地试用收件箱，不是互联网邮箱服务。
