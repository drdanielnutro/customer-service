<texto_validado_pela_deep_research_sobre_artifact>## SISTEMA DE ARTIFACTS NO PROFESSOR VIRTUAL - PROCESSAMENTO DETALHADO

### ARQUITETURA DE ARTIFACTS NO ADK

**Conceitos Fundamentais:**
1. **Artifact**: Dado binário (imagem/áudio) identificado por um filename único
2. **Representação**: Sempre como google.genai.types.Part com inline_data
3. **Storage**: Via GcsArtifactService quando em produção na Vertex.AI
4. **Namespacing**: Session-scoped (padrão) ou user-scoped (prefixo "user:")
5. **Versioning**: Automático, incrementa a cada save

### FLUXO 1: PROCESSAMENTO DE ÁUDIO

**ETAPA 1.1** - Frontend captura e prepara áudio
Frontend (Flutter) → Grava áudio → Converte para bytes → Prepara para envio


**ETAPA 1.2** - Backend recebe e cria artifact
python
# No ADK, quando o Runner recebe a requisição:
1. Runner identifica dados binários no request
2. Cria google.genai.types.Part:
   audio_part = types.Part.from_data(
       data=audio_bytes,
       mime_type="audio/wav"  # ou mp3, etc
   )
3. Salva via session context antes de passar ao agente:
   filename = f"pergunta_aluno_{timestamp}.wav"
   version = context.save_artifact(filename, audio_part)


**ETAPA 1.3** - GCS Storage (em produção)
Caminho no GCS: 
professor_virtual_app/{user_id}/{session_id}/pergunta_aluno_123.wav/0

Estrutura:
- Bucket: "adk-professor-virtual-artifacts"
- Path: app_name/user_id/session_id/filename/version
- Blob: Contém os bytes do áudio


**ETAPA 1.4** - Agente recebe referência
python
# O prompt que chega ao agente contém:
"transcreva o áudio 'pergunta_aluno_123.wav'"

# O agente NÃO recebe os bytes diretamente
# Apenas a referência (filename) para buscar via tool_context


**ETAPA 1.5** - Tool transcrever_audio acessa artifact
python
def transcrever_audio(nome_artefato_audio: str, tool_context: ToolContext):
    # 1. Tool usa o contexto para carregar o artifact
    audio_artifact = tool_context.load_artifact(nome_artefato_audio)
    
    # 2. O ADK internamente:
    #    - Identifica app_name, user_id, session_id do contexto
    #    - Constrói path GCS completo
    #    - Busca no GCS via GcsArtifactService
    #    - Retorna types.Part com os dados
    
    # 3. Tool extrai os bytes:
    if audio_artifact and audio_artifact.inline_data:
        audio_bytes = audio_artifact.inline_data.data
        mime_type = audio_artifact.inline_data.mime_type


### FLUXO 2: PROCESSAMENTO DE IMAGEM

**ETAPA 2.1** - Captura e preparação da imagem
Frontend → Captura foto → Converte para bytes → Prepara envio


**ETAPA 2.2** - Backend cria artifact da imagem
python
# Similar ao áudio:
1. Runner recebe imagem
2. Cria Part:
   image_part = types.Part.from_data(
       data=image_bytes,
       mime_type="image/png"  # ou jpeg
   )
3. Salva com contexto da pergunta:
   filename = f"exercicio_{session_id}_{timestamp}.png"
   version = context.save_artifact(filename, image_part)


**ETAPA 2.3** - Storage com contexto mantido
GCS Path:
professor_virtual_app/{user_id}/{session_id}/exercicio_abc.png/0

Importante: A imagem fica associada à MESMA sessão do áudio anterior
Isso permite que o agente correlacione pergunta + imagem


**ETAPA 2.4** - Tool analisar_imagem_educacional acessa
python
def analisar_imagem_educacional(
    nome_artefato_imagem: str, 
    contexto_pergunta: str,
    tool_context: ToolContext
):
    # Carrega artifact da sessão atual
    artifact = tool_context.session.get_artifact(nome_artefato_imagem)
    
    # No código atual usa session.get_artifact (deprecated)
    # Deveria usar: tool_context.load_artifact(nome_artefato_imagem)
    
    imagem_bytes = artifact.content  # ou artifact.inline_data.data


### FLUXO 3: GERAÇÃO DE ÁUDIO TTS

**ETAPA 3.1** - Tool gera áudio de resposta
python
def gerar_audio_tts(texto: str, tool_context: ToolContext, ...):
    # 1. Gera áudio via Gemini
    audio_bytes = _generate_tts(texto)  # processo interno
    
    # 2. Cria artifact do áudio gerado
    nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
    
    # 3. Salva na sessão
    tool_context.session.create_artifact(
        name=nome_artefato,
        content=audio_bytes,
        mime_type="audio/mpeg"
    )
    # Nota: usa API antiga, deveria ser:
    # audio_part = types.Part.from_data(audio_bytes, "audio/mpeg")
    # version = tool_context.save_artifact(nome_artefato, audio_part)


**ETAPA 3.2** - Artifact fica disponível para download
GCS Path:
professor_virtual_app/{user_id}/{session_id}/resposta_tts_xyz.mp3/0

Frontend pode:
1. Receber o filename na resposta
2. Fazer download direto do GCS (com URL assinada)
3. Ou solicitar via API do Runner


### GESTÃO DE SESSÃO E PERSISTÊNCIA

**Session-Scoped Artifacts (Padrão):**
python
# Arquivos específicos da conversa atual
"pergunta_aluno_123.wav"      # Áudio da pergunta
"exercicio_abc.png"           # Imagem do exercício
"resposta_tts_xyz.mp3"        # Áudio da resposta

# Path no GCS:
app_name/user_id/session_id/filename/version


**User-Scoped Artifacts (Persistentes):**
python
# Arquivos que persistem entre sessões
"user:historico_duvidas.json"    # Histórico do aluno
"user:preferencias_audio.json"    # Preferências de voz/velocidade
"user:avatar.png"                 # Foto do perfil

# Path no GCS:
app_name/user_id/user/filename/version


### VERSIONAMENTO AUTOMÁTICO

python
# Primeira vez que salva um arquivo
version_0 = context.save_artifact("exercicio.png", image_part)
# Retorna: 0

# Se salvar novamente com mesmo nome
version_1 = context.save_artifact("exercicio.png", new_image_part)  
# Retorna: 1

# Para carregar versão específica:
old_version = context.load_artifact("exercicio.png", version=0)
latest = context.load_artifact("exercicio.png")  # Pega a mais recente


### OTIMIZAÇÕES E CACHE

**Cache de Transcrições (implementado no código):**
python
# Em transcrever_audio.py
_transcription_cache = {}

def transcrever_audio(...):
    # Gera hash do áudio
    audio_hash = _get_audio_hash(audio_bytes)
    
    # Verifica cache antes de chamar Gemini
    if audio_hash in _transcription_cache:
        return _transcription_cache[audio_hash]
    
    # Processa e adiciona ao cache
    resultado = _process_transcription(...)
    _transcription_cache[audio_hash] = resultado


### GESTÃO DE EVENTOS E AUDIT

**Artifact Delta em Eventos:**
python
# Quando save_artifact é chamado, o ADK registra:
event.actions.artifact_delta = {
    "pergunta_aluno_123.wav": 0,      # filename: version
    "exercicio_abc.png": 0,
    "resposta_tts_xyz.mp3": 0
}

# Isso permite rastrear todos artifacts criados em uma interação


### CONFIGURAÇÃO PARA VERTEX.AI

python
# Em produção no Vertex.AI
from google.adk.artifacts import GcsArtifactService
from google.adk.runners import Runner

# Configuração do serviço
artifact_service = GcsArtifactService(
    bucket_name="adk-professor-virtual-artifacts"
)

# Runner com GCS
runner = Runner(
    agent=root_agent,
    app_name="professor_virtual_app",
    session_service=session_service,
    artifact_service=artifact_service  # GCS em vez de InMemory
)


### FLUXO COMPLETO DE REFERÊNCIAS

1. **Upload**: Frontend → Runner → GCS (via artifact_service)
2. **Referência**: Filename incluído no prompt ao agente
3. **Acesso**: Tool usa tool_context.load_artifact() → GCS
4. **Processamento**: Tool processa bytes do artifact
5. **Resultado**: Pode gerar novo artifact ou retornar dados
6. **Download**: Frontend recebe filename → Busca no GCS

Este sistema garante que dados binários grandes não trafeguem desnecessariamente, mantendo apenas referências (filenames) nas mensagens entre componentes.</texto_validado_pela_deep_research_sobre_artifacts>