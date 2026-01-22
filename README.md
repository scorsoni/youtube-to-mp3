# YT to MP3 - Conversor de YouTube para MP3

Um conversor simples e limpo de YouTube para MP3, feito em Python para uso pessoal.

## Por que este projeto existe?

Cansado de sites de conversão que:
- Sao lentos e cheios de anuncios
- Tem popups e redirecionamentos suspeitos
- Podem conter malware
- Limitam downloads ou qualidade
- Requerem cadastro ou pagamento

Este projeto resolve todos esses problemas: rapido, limpo, sem anuncios, sem limites.

## Funcionalidades

- Interface moderna com modo Light/Dark
- Conversao rapida usando yt-dlp
- FFmpeg local (sem necessidade de instalar no sistema)
- Exibicao de thumbnail, titulo e duracao do video
- Barra de progresso em tempo real
- Historico dos ultimos 5 downloads
- Download direto pelo navegador
- Validacao de URLs do YouTube
- Nomes de arquivo seguros para Windows

## Requisitos

- Python 3.10 ou superior
- FFmpeg (incluir na pasta `/bin`)

## Instalacao

### 1. Clone ou baixe o projeto

```bash
cd youtube-mp3-app
```

### 2. Instale as dependencias

```bash
pip install -r requirements.txt
```

### 3. Adicione o FFmpeg

Baixe o FFmpeg para Windows:
1. Acesse: https://www.gyan.dev/ffmpeg/builds/
2. Baixe a versao "ffmpeg-release-essentials.zip"
3. Extraia e copie `ffmpeg.exe` e `ffprobe.exe` para a pasta `/bin` do projeto

Estrutura esperada:
```
youtube-mp3-app/
├── bin/
│   ├── ffmpeg.exe    <-- NECESSARIO
│   └── ffprobe.exe   <-- OPCIONAL
```

### 4. Execute o projeto

```bash
python app.py
```

### 5. Acesse no navegador

Abra: http://localhost:5000

## Estrutura do Projeto

```
youtube-mp3-app/
│
├── app.py                 # Backend Flask
├── requirements.txt       # Dependencias Python
├── README.md              # Este arquivo
│
├── bin/                   # Binarios do FFmpeg
│   ├── ffmpeg.exe
│   └── ffprobe.exe
│
├── downloads/             # Arquivos MP3 convertidos
│
├── templates/
│   └── index.html         # Template HTML principal
│
└── static/
    ├── css/
    │   └── output.css     # Estilos customizados
    └── js/
        └── app.js         # Logica do frontend
```

## Como Usar

1. Abra o navegador em http://localhost:5000
2. Cole um link do YouTube no campo de texto
3. Clique em "Converter"
4. Aguarde o progresso (download + conversao)
5. Clique em "Baixar MP3" quando terminar

### Links suportados

- `https://www.youtube.com/watch?v=XXXXX`
- `https://youtu.be/XXXXX`
- `https://youtube.com/shorts/XXXXX`
- `https://m.youtube.com/watch?v=XXXXX`

## Endpoints da API

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/` | Pagina principal |
| POST | `/convert` | Iniciar conversao |
| GET | `/status/<id>` | Status da conversao |
| POST | `/info` | Obter info do video |
| GET | `/download/<filename>` | Baixar arquivo MP3 |
| DELETE | `/clear/<id>` | Limpar conversao |

### Exemplo de uso da API

```bash
# Iniciar conversao
curl -X POST http://localhost:5000/convert \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Resposta
{"conversion_id": "abc123", "message": "Conversao iniciada"}

# Verificar status
curl http://localhost:5000/status/abc123

# Resposta
{
  "status": "completed",
  "progress": 100,
  "filename": "Video Title.mp3",
  "filesize_formatted": "3.2 MB"
}
```

## Configuracoes

### Qualidade do Audio

Por padrao, o audio e convertido em MP3 192kbps. Para alterar, edite `app.py`:

```python
'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'mp3',
    'preferredquality': '320',  # Altere para 128, 192, 256 ou 320
}],
```

### Porta do Servidor

Para usar outra porta, edite a ultima linha de `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

## Solucao de Problemas

### "FFmpeg nao encontrado"

Certifique-se de que `ffmpeg.exe` esta na pasta `/bin` do projeto.

### "Video nao disponivel"

O video pode ser:
- Privado ou removido
- Restrito por idade (requer login)
- Bloqueado na sua regiao

### "Erro de conexao"

Verifique sua conexao com a internet e tente novamente.

### Conversao muito lenta

- Verifique sua velocidade de internet
- Videos longos demoram mais
- O servidor pode estar processando

## Aviso Legal

**Este projeto e apenas para uso pessoal e educacional.**

- Respeite os direitos autorais
- Nao use para distribuir conteudo protegido
- Baixe apenas conteudo que voce tem direito de usar
- O desenvolvedor nao se responsabiliza pelo uso indevido

## Tecnologias Utilizadas

- **Backend**: Python 3, Flask
- **Download**: yt-dlp
- **Conversao**: FFmpeg
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Icones**: Lucide Icons

## Licenca

Este projeto e de codigo aberto para uso pessoal.

---

Feito para resolver um problema pessoal: evitar sites lentos, cheios de propagandas e virus.
