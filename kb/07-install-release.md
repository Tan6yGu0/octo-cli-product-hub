# 安装 & 发布

## 安装方式

### npm
```bash
npm install -g @mininglamp-oss/octo-cli
```
npm 包解析平台子包，已包含预编译二进制，安装时不从 GitHub 下载。

来源: README.md#L55-L64

### Go install
```bash
go install github.com/Mininglamp-OSS/octo-cli/cmd/octo-cli@latest
```

来源: README.md#L66-L70

### GitHub Releases
```bash
curl -LO https://github.com/Mininglamp-OSS/octo-cli/releases/download/v<version>/octo-cli_<version>_linux_amd64.tar.gz
tar xzf octo-cli_<version>_linux_amd64.tar.gz
sudo mv octo-cli /usr/local/bin/
```

来源: README.md#L78-L92

### install.sh
```bash
curl -fsSL https://raw.githubusercontent.com/Mininglamp-OSS/octo-cli/main/install.sh | sh
```

来源: README.md#L94-L98, install.sh#L1-L81

## 发布

使用 GoReleaser，配置在 `.goreleaser.yaml`：
- 支持 linux/darwin/windows × amd64/arm64
- tar.gz 格式（含 Windows）
- SHA256 校验

来源: .goreleaser.yaml#L1-L52

## 构建

```bash
make build    # 构建 ./bin/octo-cli
make test     # go test -race -count=1 ./...
make ci       # fmt + vet + lint + test + build
```

来源: Makefile#L7-L26

## Go 版本

Go 1.24+

来源: go.mod#L3, CONTRIBUTING.md#L8
