# Frontend Integration Guidelines

Estas instruções descrevem como o aplicativo Flutter deve se comunicar com o backend ADK para realizar upload de arquivos.

```json
{
  "action": "upload_file",
  "file_data": {
    "content": "base64_encoded_content",
    "mime_type": "audio/wav",
    "filename": "pergunta_aluno_123.wav"
  },
  "session_id": "session_abc",
  "user_id": "user_123"
}
```

## O que NÃO fazer
- Esperar que o Runner crie artifacts automaticamente
- Enviar arquivos binários diretamente no corpo da requisição
- Usar APIs do ADK diretamente (não há SDK Flutter oficial)

## O que DEVE ser feito
- Converter arquivos para base64 antes de enviar
- Incluir sempre o MIME type correto
- Aguardar confirmação com `filename` e `version` do backend
