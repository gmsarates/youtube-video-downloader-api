### Como configurar
Caso o token na VPS pare de funcionar, parar o serviço

```bash
systemctl stop flaskapi
```
Rodar pelo terminal

```bash
cd /var/www/youtube-video-downloader-api
python3 main.py
```

Fazer um POST de um vídeo qualquer
Ao realizar a requisição, aparecerá no console um código para fazer login em `google.com/device`
Ao finalizar o login, apertar `ENTER` no console

Parar aplicação e subir novamente o serviço
