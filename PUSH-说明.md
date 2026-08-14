# 推送说明（PUSH-说明）

本文件记录本仓库 `resume-ai-prod` 如何把本地提交推送到 GitHub，以及踩过的坑。
供后续任何需要在本机推送/拉取的人（包括未来的自己）照着做。

---

## 0. 当前状态

- 本地仓库：`E:\简历\resume-ai-prod`（已 `git init`）
- 首个提交：`c0bbdca`（root-commit，60 个文件，约 2.9 万行）
- 分支：`master`
- 远程 `origin`：`https://github.com/zhonglufa/biographical-_notes_assistant.git`（**未含令牌**）
- 防漂移门禁：`.github/workflows/check-docs.yml`（push/PR 时自动跑 PRD↔HLD 一致性校验）

---

## 1. 为什么不在 WorkBuddy 对话里直接 `git push`

WorkBuddy 的执行环境（Bash / Git Bash）**没有公网直连出口**，`git push` / `curl https://github.com` 都会连接超时，
即使放开沙箱也不行。网页搜索/抓取能联网是因为走平台独立代理，与 Bash 出口无关。

**结论：必须在本机自己的终端（有正常公网）执行推送命令。**

---

## 2. 在本机终端推送（标准做法）

打开本机 Git Bash / PowerShell，进入仓库目录，用**内联令牌**方式推送（令牌不写入本地配置）：

```bash
cd /e/简历/resume-ai-prod
git push https://<你的PAT令牌>@github.com/zhonglufa/biographical-_notes_assistant.git master
```

- 首次推送会在 GitHub 上自动创建 `master` 分支。
- 令牌只在命令里出现一次，推送后本地 `.git/config` 里仍是**无令牌的纯地址**。
- 之后日常推送可用 `git push origin master`（若提示要凭据，用户名填 GitHub 账号、密码填 PAT；
  或先执行 `git config --global credential.helper manager` 让 Windows 凭据管理器记住）。

---

## 3. Personal Access Token 必须勾 `workflow` 权限（重要坑）

本仓库带 GitHub Actions 工作流文件 `.github/workflows/check-docs.yml`。
GitHub 规定：**用 PAT 推送会新增/修改工作流文件时，令牌必须带 `workflow` 作用域**，
否则会报：

```
! [remote rejected] master -> master
  (refusing to allow a Personal Access Token to create or update workflow
   `.github/workflows/check-docs.yml` without `workflow` scope)
```

创建/编辑 PAT 时，除 `repo` 外，**务必单独勾选 `workflow`**（经典令牌在 `repo` 下方一行）。
编辑作用域后原令牌字符串不变，直接重跑第 2 节的命令即可。

> 若不想给 `workflow` 权限，只能先把工作流文件从提交里移除再推——不推荐，会丢失 CI 门禁。

---

## 4. 国内网络连不上 GitHub（errno 10054 / Connection reset）

若报错 `OpenSSL SSL_read: Connection was reset, errno 10054`，通常是网络层（防火墙/代理）把到 `github.com:443` 的连接重置。
按从简到繁尝试：

1. **直接重试** 2–3 次（可能是瞬时抖动）。
2. **走公共中继**（仅本次生效，不改本地配置）：
   ```bash
   git -c url."https://ghproxy.com/https://github.com/".insteadOf="https://github.com/" \
       push https://<你的PAT令牌>@github.com/zhonglufa/biographical-_notes_assistant.git master
   ```
   若 `ghproxy.com` 连不上，换 `kgithub.com` 镜像：
   ```bash
   git -c url."https://kgithub.com/".insteadOf="https://github.com/" \
       push https://<你的PAT令牌>@github.com/zhonglufa/biographical-_notes_assistant.git master
   ```
   > 令牌会经中继转发到 GitHub；个人项目一般可接受，推完即止。
3. **换网络 / 开 VPN**：手机热点给电脑，或开 VPN 后重试第 2 节命令。

---

## 5. 令牌安全要点

- 优先用**内联令牌**推送，推送后 `git remote -v` 应显示无令牌的纯地址。
- 临时用完后，可在 GitHub → Settings → Developer settings → PAT 里**删除或轮换**令牌，不影响已上传代码。
- 不要把真实令牌写进任何会被提交的文档/脚本（本文件用 `<你的PAT令牌>` 占位）。
- 若曾把令牌嵌进 `origin` 地址，用下面命令抹掉：
  ```bash
  git remote set-url origin https://github.com/zhonglufa/biographical-_notes_assistant.git
  ```

---

## 6. 推送成功后

- GitHub 上自动建出 `master` 分支，并**自动触发** Actions 运行 `check-docs.yml`（PRD↔HLD 防漂移校验）。
- 在仓库 **Actions** 标签页查看结果，全绿即通过。
- 后续修改 PRD / HLD 后提交，pre-commit 钩子（本地）与 CI（远程）都会再次校验对齐。

---

## 7. 快速检查清单

- [ ] 本机终端、有公网
- [ ] PAT 已勾 `repo` **且** `workflow`
- [ ] 推送命令用的是内联令牌（非存进 `origin`）
- [ ] 若 10054，先重试，再试 ghproxy / kgithub 中继，或换网络
- [ ] 推送后 `git remote -v` 确认 origin 无令牌
- [ ] 去 Actions 看校验结果
