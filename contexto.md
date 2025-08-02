# Professor Virtual - Contexto do Projeto

- **Backend**: Python com Google ADK
  - Framework: ADK Runner com artifacts assíncronos
  - APIs: Gemini Pro para processamento de linguagem e visão
  - Armazenamento: GCS (Google Cloud Storage) em produção, InMemory em desenvolvimento
  - Importante: as capacidades do modo "produção" e do modo "desenvolvimento" devem coexistir.
  
- **Frontend**: Flutter (mobile/web) - ainda não implementado, estamos justamente preparando tudo para a implementação.
  - Comunição via HTTP REST com o backend ADK.
  - Suporte para reprodução e gravação de áudio, suporte para câmera (tirar foto e enviar imagem).
  - As respostas do backend deverão alterar setores da UI (UI dinâmica, estilo 'Canvas')

**Nota sobre Uploads**: Sistema de upload ainda não está operacional. Veja `PLANO_UPLOAD_GCS.md` para arquitetura proposta.

#### Diretório Raiz (professor-virtual/)
- **professor_virtual/**: Módulo principal contendo toda a lógica do agente educacional
- **deployment/**: Scripts e configurações para implantação em produção
- **eval/**: Testes de avaliação para validar o comportamento do agente
- **tests/**: Testes unitários para garantir qualidade do código
- **pyproject.toml**: Arquivo de configuração do projeto Python (dependências, metadados)
- **README.md**: Documentação principal do projeto

#### Módulo Principal (professor_virtual/)
- **__init__.py**: Arquivo que marca o diretório como um pacote Python
- **agent.py**: Lógica principal do agente - coordena todas as interações e decisões do professor virtual
- **config.py**: Configurações do sistema (URLs, credenciais, parâmetros)
- **prompts/**: Sistema de instruction providers para personalização dinâmica do comportamento
  - **prompts.py**: Providers dinâmicos que adaptam as instruções conforme o contexto
  - **README.md**: Documentação sobre como criar e usar os providers
- **entities/**: Modelos de dados (classes para representar alunos, lições, etc.)
- **shared_libraries/**: Código compartilhado entre diferentes componentes

#### Ferramentas Educacionais (tools/)
Cada ferramenta está organizada em seu próprio subdiretório:

1. **transcrever_audio/**
   - **Função**: Converte áudio do aluno em texto usando Gemini API
   - **Uso**: Permite que o aluno faça perguntas por voz
   - **Entrada**: Arquivo de áudio (wav, mp3, etc.)
   - **Saída**: Texto transcrito da fala

2. **analisar_necessidade_visual/**
   - **Função**: Determina se uma resposta precisa de apoio visual
   - **Uso**: Decide quando gerar diagramas ou imagens explicativas
   - **Entrada**: Contexto da conversa e pergunta do aluno
   - **Saída**: Boolean indicando necessidade + tipo de visual sugerido

3. **analisar_imagem_educacional/**
   - **Função**: Analisa imagens enviadas pelo aluno (exercícios, dúvidas)
   - **Uso**: Corrige trabalhos fotografados, identifica erros em diagramas
   - **Entrada**: Imagem + contexto educacional
   - **Saída**: Análise detalhada com feedback pedagógico

4. **gerar_audio_tts/**
   - **Função**: Converte texto em áudio falado (Text-to-Speech)
   - **Uso**: Permite respostas em áudio para alunos com dificuldades de leitura
   - **Entrada**: Texto a ser falado + parâmetros de voz
   - **Saída**: Arquivo de áudio com a fala sintetizada

5. **upload_arquivo/**
   - **Função**: Processa uploads de arquivos do frontend e cria artifacts ADK
   - **Uso**: Recebe arquivos (áudio/imagem) e os prepara para processamento
   - **Entrada**: URI do arquivo no GCS + metadados
   - **Saída**: Confirmação com versão do artifact criado
   - **Status**: Implementada, aguarda servidor híbrido para funcionar

## Arquitetura de Upload (Em Implementação) ****

**Desafio**: O ADK não expõe endpoints HTTP nativos para upload de arquivos.

**Solução Proposta**: Servidor híbrido com Signed URLs do Google Cloud Storage
- Frontend solicita URL temporária para upload
- Upload direto para GCS (não passa pelo servidor)
- Backend processa arquivo via tool upload_arquivo

**Status**: Plano detalhado em `PLANO_UPLOAD_GCS.md`

**Próximos Passos**:
1. Implementar servidor híbrido (hybrid_server.py)
2. Configurar bucket GCS e permissões
3. Atualizar tool para processar URIs do GCS
4. Testar fluxo completo com frontend

<upload_arquivos_gcs_adk>
**** Anexo sobre Upload de arquivos no GCS e Artifacts no ADK do Google:
Guia Completo: Upload de Arquivos e Gerenciamento de Artifacts no Google ADK

  Visão Geral

  Este guia explica como implementar corretamente o upload de arquivos e o gerenciamento de artifacts em aplicações que utilizam o Google Assistant Development Kit (ADK). A compreensão
  clara da diferença entre "arquivos no storage" e "artifacts ADK" é fundamental para evitar problemas de performance e custos desnecessários.

  Conceitos Fundamentais

  O que são Artifacts ADK?

  Artifacts ADK são dados gerados pelo seu agent durante o processamento que precisam ser persistidos e versionados. Eles são gerenciados automaticamente pelo ADK através do ArtifactService
   e incluem:
  - Versionamento automático
  - Namespace por usuário/sessão
  - Integração com o contexto da ferramenta

  Exemplos de artifacts: áudio gerado por TTS, resultado de uma análise, documento processado.

  O que são Arquivos no GCS?

  Arquivos no Google Cloud Storage (GCS) são dados armazenados diretamente no storage, sem gerenciamento do ADK. Quando o frontend faz upload de um arquivo, ele vai direto para o GCS e
  permanece lá como um arquivo comum.

  Exemplos: foto enviada pelo usuário, áudio gravado, documento para análise.

  Diferença entre URI e URL

  - URI (Uniform Resource Identifier): Identificador genérico de recurso
    - Exemplo: gs://meu-bucket/pasta/arquivo.wav
    - Usado internamente pelas APIs do Google
  - URL (Uniform Resource Locator): Endereço web completo
    - Exemplo: https://storage.googleapis.com/meu-bucket/pasta/arquivo.wav
    - Usado para acesso via HTTP/HTTPS

  Filosofia Central: "O arquivo já está no destino final"

  Quando um arquivo é enviado para o GCS através de Signed URLs, ele já está em seu local de armazenamento definitivo. Não há necessidade de movê-lo, copiá-lo ou transformá-lo em artifact.
  As tools devem apenas referenciar sua localização.

  Arquitetura de Upload com Signed URLs

  Por que Signed URLs?

  O ADK não expõe endpoints HTTP nativos para upload de arquivos. A solução é criar um servidor híbrido que:
  1. Gera URLs temporárias e seguras para upload
  2. Permite que o frontend faça upload direto para o GCS
  3. Mantém a segurança através de URLs com tempo de expiração

  Fluxo Completo de Upload (3 passos)

  Passo 1: Frontend Solicita URL de Upload

  // Frontend (Flutter/JavaScript)
  const response = await fetch('https://seu-servidor.com/api/get-upload-url', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      filename: 'gravacao_aula.wav',
      user_id: 'user123',
      session_id: 'session456',
      mime_type: 'audio/wav'
    })
  });

  const data = await response.json();
  // data contém:
  // {
  //   "upload_url": "https://storage.googleapis.com/bucket/...",  // Para fazer upload
  //   "gcs_uri": "gs://bucket/user123/session456/gravacao_aula.wav", // Para referenciar
  //   "expires_in": 900  // 15 minutos
  // }

  Passo 2: Upload Direto para GCS

  // Frontend faz PUT diretamente no GCS
  const uploadResponse = await fetch(data.upload_url, {
    method: 'PUT',
    headers: {'Content-Type': 'audio/wav'},
    body: audioBlob  // Os bytes do arquivo
  });

  if (uploadResponse.ok) {
    console.log('Upload concluído!');
  }

  Passo 3: Invocar o Agent com a Referência

  // Frontend informa o backend sobre o arquivo
  const agentResponse = await fetch('https://seu-servidor.com/invoke', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      user_id: 'user123',
      session_id: 'session456',
      prompt: 'Transcreva o áudio que enviei',
      files: [{
        uri: data.gcs_uri,  // Passa o URI, não a URL!
        mime_type: 'audio/wav',
        filename: 'gravacao_aula.wav'
      }]
    })
  });

  Implementação do Backend

  Servidor Híbrido (hybrid_server.py)

  from google.adk.cli.fast_api import get_fast_api_app
  from google.cloud import storage
  from datetime import timedelta
  from fastapi import HTTPException
  import os

  # Cliente GCS
  storage_client = storage.Client()
  bucket_name = os.getenv("GCS_BUCKET_NAME", "meu-bucket-uploads")
  bucket = storage_client.bucket(bucket_name)

  # App híbrido ADK + FastAPI
  app = get_fast_api_app(
      agent_dir="./",
      session_db_url="sqlite:///sessions.db",
      allow_origins=["*"]
  )

  @app.post("/api/get-upload-url")
  async def get_upload_url(
      filename: str,
      user_id: str,
      session_id: str,
      mime_type: str
  ):
      """Gera URL assinada para upload direto ao GCS"""

      # Validação de segurança
      if ".." in filename or "/" in filename or "\\" in filename:
          raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

      # Criar caminho único no bucket
      blob_name = f"{user_id}/{session_id}/{filename}"
      blob = bucket.blob(blob_name)

      # Gerar signed URL para upload
      signed_url = blob.generate_signed_url(
          version="v4",
          expiration=timedelta(minutes=15),
          method="PUT",
          content_type=mime_type
      )

      return {
          "upload_url": signed_url,
          "gcs_uri": f"gs://{bucket_name}/{blob_name}",
          "expires_in": 900
      }

  Tool que Processa o Arquivo Enviado

  from google.adk.tools import tool, ToolContext
  from google import genai
  from google.genai import types
  import json

  @tool(
      name="transcrever_audio_enviado",
      description="Transcreve áudio que foi enviado pelo usuário"
  )
  async def transcrever_audio_enviado(
      gcs_uri: str,
      context: ToolContext
  ) -> Dict[str, Any]:
      """
      Transcreve áudio usando referência do GCS.
      
      IMPORTANTE: Esta tool NÃO baixa o arquivo nem cria artifact.
      Ela processa diretamente do GCS.
      """
      try:
          # Cliente Gemini
          client = genai.Client()

          # File API aceita GCS URI diretamente!
          # Isso NÃO baixa o arquivo, apenas cria uma referência
          audio_file = client.files.upload(file=gcs_uri)

          # Processar com Gemini
          response = client.models.generate_content(
              model='gemini-2.5-flash',
              contents=[
                  audio_file,
                  "Transcreva este áudio em português brasileiro"
              ],
              config=types.GenerateContentConfig(
                  temperature=0.1,
                  response_mime_type='application/json'
              )
          )

          # Parse da resposta
          transcricao = json.loads(response.text)

          # IMPORTANTE: Aqui podemos salvar o RESULTADO como artifact
          # porque é um dado NOVO gerado pela tool
          resultado_artifact = types.Part.from_text(
              text=transcricao['texto']
          )

          version = await context.save_artifact(
              filename=f"transcricao_{context.session_id}.txt",
              artifact=resultado_artifact
          )

          return {
              "sucesso": True,
              "transcricao": transcricao['texto'],
              "gcs_uri_original": gcs_uri,
              "artifact_transcricao": f"transcricao_{context.session_id}.txt",
              "versao": version
          }

      except Exception as e:
          return {
              "sucesso": False,
              "erro": str(e)
          }

  Quando Usar save_artifact()

  ✅ USE save_artifact() quando:

  1. Gerando novo conteúdo
  # Áudio TTS gerado
  audio_data = gerar_audio_tts("Olá aluno")
  await context.save_artifact("resposta_audio.wav", audio_data)
  2. Resultado de processamento
  # Transcrição gerada
  transcricao = transcrever_audio(audio_uri)
  await context.save_artifact("transcricao.txt", transcricao)
  3. Análise criada
  # Análise de imagem
  analise = analisar_imagem_educacional(imagem_uri)
  await context.save_artifact("analise_imagem.json", analise)

  ❌ NÃO USE save_artifact() quando:

  1. Arquivo já existe no GCS
  # ERRADO!
  blob = download_from_gcs(gcs_uri)
  await context.save_artifact("copia.bin", blob)  # Duplo upload!
  2. Referenciando arquivo enviado
  # ERRADO!
  # O arquivo já está no GCS, não precisa virar artifact
  await context.save_artifact("upload_usuario.jpg", gcs_uri)

  Fluxo Completo: Upload vs Geração

  Cenário 1: Upload de Arquivo pelo Usuário

  1. Frontend solicita Signed URL
     POST /api/get-upload-url

  2. Backend retorna:
     {
       "upload_url": "https://storage.googleapis.com/...",
       "gcs_uri": "gs://bucket/user123/session456/foto.jpg"
     }

  3. Frontend faz upload direto:
     PUT https://storage.googleapis.com/... (com os bytes)

  4. Frontend invoca agent:
     POST /invoke
     {
       "prompt": "Analise esta imagem",
       "files": [{"uri": "gs://bucket/user123/session456/foto.jpg"}]
     }

  5. Backend processa:
     - USA o URI diretamente com Gemini
     - NÃO cria artifact do arquivo original
     - PODE criar artifact do resultado da análise

  Cenário 2: Geração de Conteúdo pelo Agent

  1. Frontend invoca agent:
     POST /invoke
     {
       "prompt": "Gere um áudio dizendo: Parabéns pelo exercício!"
     }

  2. Backend processa:
     - Tool gera_audio_tts cria o áudio
     - USA save_artifact() para salvar o áudio gerado
     - Retorna nome do artifact

  3. Frontend baixa artifact:
     GET /artifacts/resposta_tts_abc123.wav

  Configuração do Google Cloud Storage

  1. Criar Bucket

  gsutil mb gs://meu-projeto-uploads

  2. Configurar CORS para Upload do Browser

  [
    {
      "origin": ["*"],
      "method": ["PUT"],
      "maxAgeSeconds": 3600
    }
  ]

  gsutil cors set cors.json gs://meu-projeto-uploads

  3. Service Account e Permissões

  # Permissões mínimas necessárias
  gsutil iam ch serviceAccount:sa@project.iam.gserviceaccount.com:roles/storage.objectCreator gs://meu-projeto-uploads
  gsutil iam ch serviceAccount:sa@project.iam.gserviceaccount.com:roles/storage.objectViewer gs://meu-projeto-uploads

  4. Variáveis de Ambiente (.env)

  GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
  GCS_BUCKET_NAME=meu-projeto-uploads
  GOOGLE_CLOUD_PROJECT=meu-projeto-id

  Considerações para Deploy em Produção

  Opção 1: Cloud Run (Recomendado para Início)

  - Deploy único do servidor híbrido
  - Suporta endpoints customizados
  - Mais simples de gerenciar

  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["python", "run_hybrid.py"]

  Opção 2: Vertex AI (Produção Escalável)

  Requer arquitetura com 2 serviços separados:

  1. Serviço de URLs (Cloud Run)
    - Apenas o endpoint /api/get-upload-url
    - Responsável por gerar Signed URLs
  2. Agent ADK (Vertex AI)
    - Endpoints padrão do ADK (/invoke, etc.)
    - Processa as requisições do agent

  Erros Comuns e Como Evitar

  1. Anti-pattern do Duplo Upload

  # ❌ ERRADO
  blob = storage.Blob.from_string(gcs_uri, client=storage_client)
  content = blob.download_as_bytes()  # Baixa desnecessariamente
  await context.save_artifact("copia", content)  # Re-upload!

  # ✅ CORRETO
  client = genai.Client()
  arquivo = client.files.upload(file=gcs_uri)  # Apenas referencia

  2. Endpoint de Confirmação Desnecessário

  # ❌ ERRADO
  @app.post("/api/confirm-upload")
  async def confirm_upload(gcs_uri: str):
      # Endpoint intermediário desnecessário
      return await invoke_agent(gcs_uri)

  # ✅ CORRETO
  # Frontend chama /invoke diretamente após upload

  3. Contexto Errado para Artifacts

  # ❌ ERRADO
  from google.adk.agents.invocation_context import InvocationContext
  async def minha_funcao(context: InvocationContext):
      await context.save_artifact(...)  # InvocationContext não tem esse método!

  # ✅ CORRETO
  from google.adk.tools import ToolContext
  async def minha_tool(context: ToolContext):
      await context.save_artifact(...)  # ToolContext tem o método

  4. Processar Localmente sem Necessidade

  # ❌ ERRADO
  import librosa
  audio_data = download_from_gcs(gcs_uri)
  resultado = librosa.load(audio_data)  # Processamento local

  # ✅ CORRETO
  # Use Gemini que aceita GCS URI diretamente
  arquivo = client.files.upload(file=gcs_uri)
  response = client.models.generate_content(...)

  Resumo das Melhores Práticas

  1. Arquivos enviados pelo usuário: Permanecem no GCS como arquivos comuns
  2. Dados gerados pelo agent: São salvos como artifacts via save_artifact()
  3. URIs não são artifacts: São apenas referências a arquivos no storage
  4. Gemini File API: Aceita GCS URIs diretamente, sem download
  5. Signed URLs: Solução segura para upload direto do frontend
  6. Vertex AI: Requer serviços separados para URLs customizadas
</upload_arquivos_gcs_adk>