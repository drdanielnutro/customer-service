# MAPEAMENTO COMPLETO PÓS-CORREÇÕES – PROFESSOR VIRTUAL 
---

## VISÃO GERAL

1. **Audição → Transcrição** (com artifacts assíncronos)
2. **Análise de texto → Decisão visual** (ferramentas async)
3. **Captura de imagem (opcional)**
4. **Upload → Criação explícita de artifact**
5. **Análise de imagem (opcional)** (load_artifact assíncrono)
6. **Geração de resposta** (text/plain - pendente refatoração para JSON estruturado)
7. **TTS sob demanda** (save_artifact assíncrono)

> **Ambientes de Execução**
> - **Dev**: `InMemoryArtifactService` - artifacts voláteis
> - **Prod**: `GcsArtifactService` - persistência em `gs://adk-professor-virtual-artifacts`

---

## 1. FLUXO: INÍCIO DA INTERAÇÃO – AÇÃO DE FALAR

| Etapa   | Ação               | Ator              | Detalhes                                          |
| ------- | ------------------ | ----------------- | ------------------------------------------------- |
| **1.1** | Pressionar botão 🎙 | Usuário (criança) | Mantém pressionado ⇒ inicia captura de áudio      |
| **1.2** | Captura contínua   | Frontend          | Grava áudio enquanto o botão está pressionado     |
| **1.3** | Soltar botão       | Usuário           | Frontend encerra a gravação e gera arquivo `.wav` |

---

## 2. FLUXO: UPLOAD E TRANSCRIÇÃO DA FALA

| Etapa   | Ação                          | Ator                                       | Dados / Código                                                                                                                                                               | Resultado                              |
| ------- | ----------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| **2.1** | Empacotar áudio               | Frontend                                   | Base64 encode + JSON:<br>`{content, mime_type, filename}`                                                                                                                    | Payload pronto                         |
| **2.2** | **POST** `/upload`            | Frontend → Backend                         | Envia JSON para endpoint                                                                                                                                                     | Backend recebe dados                   |
| **2.3** | Criar artifact explicitamente | Backend (`artifact_handler.py`)            | ```python<br>artifact = types.Part.from_data(<br>    data=audio_bytes,<br>    mime_type="audio/wav"<br>)<br>version = await context.save_artifact(filename, artifact)<br>``` | Retorna `{filename, version, success}` |
| **2.4** | Confirmar upload              | Frontend                                   | Recebe resposta com versão                                                                                                                                                   | Armazena metadata                      |
| **2.5** | Transcrever áudio             | Backend<br>(`async def transcrever_audio`) | ```python<br>audio_artifact = await tool_context.load_artifact(nome_artefato_audio)<br>audio_bytes = audio_artifact.inline_data.data<br>```                                  | Retorna `{sucesso, texto, versao}`     |

---

## 3. FLUXO: ANÁLISE DE TEXTO E DECISÃO VISUAL

| Etapa   | Ação                        | Ator                                                 | Código / Lógica                                                                                  | Resultado                       |
| ------- | --------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------- |
| **3.1** | Detectar necessidade visual | Backend<br>(`async def analisar_necessidade_visual`) | Procura padrões: "esse exercício aqui", "olha isso"                                              | `{necessita_imagem, confianca}` |
| **3.2** | Decidir próxima ação        | Agent (root_agent)                                   | **Se** `necessita_imagem: true` ⇒ responde texto solicitando imagem<br>**Senão** ⇒ gera resposta | Resposta em text/plain          |

---

## 4. FLUXO: CAPTURA DE IMAGEM (OPCIONAL)

| Etapa     | Ação            | Ator     | Detalhes                                |
| --------- | --------------- | -------- | --------------------------------------- |
| **4.1**   | Abrir câmera    | Frontend | Imediato, sem pop-up de confirmação     |
| **4.2**   | Preview ao vivo | Frontend | Exibe stream da câmera                  |
| **4.3.A** | Capturar 📷      | Usuário  | Foto instantânea, sem preview posterior |
| **4.3.B** | Fechar X        | Usuário  | Cancela; frontend notifica backend      |

---

## 5. FLUXO: UPLOAD E ANÁLISE DA IMAGEM

| Etapa   | Ação                   | Ator                                                 | Código / Dados                                                                                                                                                                   | Resultado                                        |
| ------- | ---------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **5.1** | Empacotar imagem       | Frontend                                             | Base64 + JSON com `contexto_pergunta`                                                                                                                                            | Payload pronto                                   |
| **5.2** | **POST** `/upload`     | Frontend → Backend                                   | JSON para `artifact_handler.py`                                                                                                                                                  | Backend processa                                 |
| **5.3** | Criar artifact imagem  | Backend (`handle_file_upload`)                       | ```python<br>image_part = types.Part.from_data(<br>    data=image_bytes,<br>    mime_type="image/png"<br>)<br>version = await context.save_artifact(filename, image_part)<br>``` | `{filename, version, success}`                   |
| **5.4** | Analisar imagem        | Backend<br>(`async def analisar_imagem_educacional`) | ```python<br>artifact = await tool_context.load_artifact(nome_artefato_imagem)<br>imagem_bytes = artifact.inline_data.data<br>```                                                | `{tipo_conteudo, elementos_detectados, sucesso}` |
| **5.5** | Fallback se inadequada | Backend                                              | Se `qualidade_adequada: false` ⇒ solicita nova foto                                                                                                                              | Mensagem apropriada                              |

---

## 6. FLUXO: GERAÇÃO DA RESPOSTA

| Etapa   | Ação              | Ator               | Configuração Atual                                                                                                       | Saída                             |
| ------- | ----------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| **6.1** | Combinar contexto | Backend (Agent)    | Texto transcrito + análise da imagem                                                                                     | Resposta pedagógica estruturada   |
| **6.2** | Enviar resposta   | Backend → Frontend | ```python<br>generate_content_config: {<br>    "response_mime_type": "text/plain"  # ⚠️ Problema identificado<br>}<br>``` | String de texto (não estruturado) |

> **Nota**: A configuração atual retorna `text/plain`. Uma futura iteração deve implementar resposta JSON estruturada.

---

## 7. FLUXO: APRESENTAÇÃO & ÁUDIO TTS

| Etapa   | Ação                  | Ator                                     | Código / Detalhes                                                                                                                                                                           | Resultado                                 |
| ------- | --------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| **7.1** | Exibir texto          | Frontend                                 | Renderiza resposta na tela                                                                                                                                                                  | Texto visível                             |
| **7.2** | Tocar som curto       | Frontend                                 | Áudio local "Prontinho!" (não é artifact)                                                                                                                                                   | Notificação sonora                        |
| **7.3** | Mostrar botão ▶️       | Frontend                                 | Lógica local baseada no tamanho do texto                                                                                                                                                    | UI condicional                            |
| **7.4** | Gerar TTS sob demanda | Backend<br>(`async def gerar_audio_tts`) | ```python<br>audio_part = types.Part.from_data(<br>    data=audio_bytes,<br>    mime_type="audio/mpeg"<br>)<br>version = await tool_context.save_artifact(nome_artefato, audio_part)<br>``` | `{nome_artefato_gerado, versao, sucesso}` |
| **7.5** | Download do áudio     | Frontend                                 | Solicita artifact via API usando filename + version                                                                                                                                         | Stream de áudio MP3                       |

---

## 8. CONFIGURAÇÃO DO SISTEMA

### 8.1 Inicialização do Runner (agent.py)

```python
# Configuração do artifact service
if configs.is_production and configs.artifact_storage_type == "gcs":
    artifact_service = GcsArtifactService(bucket_name=configs.gcs_bucket_name)
else:
    artifact_service = InMemoryArtifactService()

# Runner com todos os serviços
runner = Runner(
    agent=root_agent,
    app_name=configs.app_name,
    session_service=session_service,
    artifact_service=artifact_service  # OBRIGATÓRIO
)
```

### 8.2 Estrutura de Armazenamento GCS (Produção)

```
gs://adk-professor-virtual-artifacts/
├── professor_virtual_app/
│   └── {user_id}/
│       └── {session_id}/
│           ├── pergunta_aluno_123.wav/
│           │   └── 0  # versão
│           ├── exercicio_abc.png/
│           │   └── 0
│           └── resposta_tts_xyz.mp3/
│               └── 0
```

---

## 9. CHECKLIST DE CONFORMIDADE PÓS-CORREÇÕES

| Item                    | Status | Implementação                                       |
| ----------------------- | ------ | --------------------------------------------------- |
| **Tools assíncronas**   | ✅      | Todas com `async def`                               |
| **APIs corretas**       | ✅      | `await load_artifact()`, `await save_artifact()`    |
| **Sem APIs deprecated** | ✅      | Removidos `session.get_artifact`, `create_artifact` |
| **Artifact service**    | ✅      | Configurado no Runner                               |
| **Criação explícita**   | ✅      | Via `handle_file_upload` + `types.Part.from_data()` |
| **Acesso aos dados**    | ✅      | Via `artifact.inline_data.data`                     |
| **Versionamento**       | ✅      | Retornado em cada `save_artifact()`                 |
| **Frontend base64**     | ✅      | Converte antes de enviar                            |
| **MIME types**          | ✅      | Sempre especificados                                |

---

## 10. PONTOS DE ATENÇÃO FUTUROS

1. **Resposta estruturada**: Migrar de `text/plain` para JSON com campo `action`
2. **URLs assinadas**: Implementar download direto do GCS
3. **Limpeza de artifacts**: Política de retenção para produção
4. **Cache de transcrições**: Já implementado, monitorar performance

---