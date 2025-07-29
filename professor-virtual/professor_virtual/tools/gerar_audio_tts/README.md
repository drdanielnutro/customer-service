# Ferramenta gerar_audio_tts

## Descrição

A ferramenta `gerar_audio_tts` é responsável por converter texto em áudio usando a API Text-to-Speech (TTS) do Google Gemini. Ela recebe um texto como entrada e retorna um arquivo de áudio WAV salvo como artifact no ADK.

## Funcionalidades

- Converte texto em áudio usando o modelo `gemini-2.5-flash-preview-tts`
- Suporta 30 vozes diferentes do Gemini
- Salva o áudio gerado como artifact ADK
- Converte dados PCM para formato WAV
- Validação de entrada e tratamento de erros

## Atualizações Realizadas (2025-07-29)

### 1. Conversão para Função Assíncrona

**Mudança**: `def gerar_audio_tts` → `async def gerar_audio_tts`

**Motivo**: O método `save_artifact` do ADK é assíncrono, conforme documentado em [ADK Artifacts](https://google.github.io/adk-docs/artifacts/):
```python
version = await context.save_artifact(filename=filename, artifact=report_artifact)
```

### 2. Correção do Processamento de Dados de Áudio

**Problema**: O código assumia incorretamente que os dados vinham codificados em base64:
```python
# INCORRETO
audio_data_base64 = audio_part.inline_data.data
pcm_data = base64.b64decode(audio_data_base64)
```

**Solução**: Os dados já vêm como bytes diretos, conforme [documentação oficial da API TTS](https://google.github.io/adk-docs/streaming/custom-streaming/):
```python
# CORRETO
pcm_data = audio_part.inline_data.data
```

### 3. Atualização do Método de Salvamento de Artifact

**Antes**: Usava método não documentado `tool_context.session.create_artifact()`

**Depois**: Usa método oficial ADK `tool_context.save_artifact()`, conforme [ADK Artifacts](https://google.github.io/adk-docs/artifacts/):
```python
audio_artifact = types.Part.from_bytes(
    data=audio_bytes,
    mime_type="audio/wav"
)
version = await tool_context.save_artifact(
    filename=nome_artefato,
    artifact=audio_artifact
)
```

### 4. Melhorias Adicionais

- **Captura de mime_type**: Agora captura o mime_type retornado pela API
- **Logging**: Adicionado para facilitar debug
- **Retorno expandido**: Inclui versão do artifact e mime_type original
- **Função `_create_wav_from_pcm`**: Atualizada para aceitar mime_type como parâmetro

## Estrutura de Retorno

```python
{
    "sucesso": True,                          # Indica se a operação foi bem-sucedida
    "nome_artefato_gerado": "resposta_tts_*.wav",  # Nome do arquivo gerado
    "tamanho_caracteres": int,                # Tamanho do texto original
    "tamanho_bytes": int,                     # Tamanho do arquivo de áudio
    "voz_utilizada": str,                     # Nome da voz Gemini usada
    "versao_artefato": int,                   # Versão do artifact (NOVO)
    "mime_type_original": str                 # MIME type original da API (NOVO)
}
```

Em caso de erro:
```python
{
    "sucesso": False,
    "erro": str,                              # Mensagem de erro
    "tipo_erro": str                          # Tipo da exceção (opcional)
}
```

## Vozes Disponíveis

A ferramenta suporta 30 vozes do Gemini:
- Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede
- Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba
- Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar
- Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi
- Vindemiatrix, Sadachbia, Sadaltager, Sulafat

## Compatibilidade

### Com o Projeto
- Mantém todos os campos originais de retorno
- Compatível com ferramentas síncronas existentes
- Não requer mudanças em `agent.py` ou `config.py`

### Com o ADK
- Segue as práticas recomendadas para artifacts
- Usa métodos oficiais documentados
- Suporta execução assíncrona conforme [ADK Runtime](https://google.github.io/adk-docs/runtime/)

## Referências

- [ADK Artifacts Documentation](https://google.github.io/adk-docs/artifacts/)
- [ADK Runtime Documentation](https://google.github.io/adk-docs/runtime/)
- [Gemini TTS Documentation](.desenvolvedor/documentacao_adk/doc_gemini_modelos/api_text_to_speach.md)
- [Google Studio TTS Examples](https://aistudio.google.com/)

## Notas Técnicas

### Formato de Áudio
- **Entrada da API**: PCM bruto (24kHz, 16-bit, mono)
- **Saída da ferramenta**: WAV (com headers apropriados)

### Limites
- Limite de contexto: 32k tokens
- Tamanho máximo recomendado: Definido pela API Gemini

### Dependências
```bash
pip install google-adk>=1.5.0 google-genai>=0.3.0 python-dotenv
```