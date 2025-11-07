## certbot-rainyun-auth

用于 certbot 通配符域名证书自动创建与刷新的 hook 脚本，仅支持雨云的 DNS 产品。使用的认证方式为 DNS-01。

### 用法

推荐通过`pyinstaller`等方式将代码打包为可执行文件使用。

1. **获取雨云账号 API Key**
   使用浏览器登录你的雨云账号，在右上角用户头像下拉菜单中进入“用户设置”。
   
   <img src="https://raw.githubusercontent.com/softmanmaker/certbot-rainyun-auth/refs/heads/main/assets/image.png" height="250">
   
   之后进入“API 密钥”选项，如果还没有显示密钥，点击“重新生成”即可看到密钥，记住显示的 API 密钥。
   
   <img src="https://raw.githubusercontent.com/softmanmaker/certbot-rainyun-auth/refs/heads/main/assets/image-1.png" height="200">
3. **获取 DNS 产品 ID**
   进入“域名管理”界面，选择你想要配置证书的域名产品，并记住其产品 ID。
   
   <img src="https://raw.githubusercontent.com/softmanmaker/certbot-rainyun-auth/refs/heads/main/assets/image-2.png" height="150">
5. **进行证书创建与自动更新相关配置**
   在命令行中以 root 身份运行如下命令（可能会需要 sudo）：
   ```bash
    certbot certonly \
        --manual \
        --preferred-challenges dns \
        --manual-auth-hook "python3 </path/to/main.py> auth -k <your_api_key> -i <domain> <id>" \
        --manual-cleanup-hook "python3 </path/to/main.py> clear -k <your_api_key> -i <domain> <id>" \
        -d <your.domain> \
        -d <*.your.domain>
   ```
   其中`-i <domain> <id>`与`-d <domain>`部分可以重复任意次，以实现多 DNS 产品的证书自动化。
   完成后，将下方命令加入 root 用户的 crontab，以实现证书定期更新。
   ```bash
    certbot renew --quiet \
        --force-renewal \
        --manual-auth-hook "python3 </path/to/main.py> auth -k <your_api_key> -i <domain> <id>" \
        --manual-cleanup-hook "python3 </path/to/main.py> clear -k <your_api_key> -i <domain> <id>"
   ```
   同时，也要记得配合更新定期重启反代服务，保证证书正确。

**注意**：如果你不想把你的 API Key 写在命令当中，则也可以通过环境变量方式传递。在命令行参数不包含`-k`的情况下，程序会尝试读取环境变量`RAINYUN_APIKEY`。
