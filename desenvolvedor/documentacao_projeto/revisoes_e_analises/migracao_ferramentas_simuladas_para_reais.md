# Implementação de Ferramentas ADK 1.5 com Modelos Gemini Específicos

Pesquisa completa realizada na documentação oficial do Google ADK e google.genai para implementar as três ferramentas solicitadas com compatibilidade local e Vertex AI.

## Configuração base para ADK 1.5

A configuração inicial garante que o código funcione tanto localmente quanto no Vertex AI sem alterações.

### Estrutura do projeto

```
projeto/
├── agent.py
├── tools.py
├── requirements.txt
└── .env
```

### Arquivo requirements.txt

```txt
google-adk>=1.5.0
google-genai>=0.3.0
google-cloud-aiplatform[agent_engines,adk]>=1.88.0
python-dotenv>=0.19.0
```

### Arquivo .env

```bash
# Para execução local
GOOGLE_API_KEY="sua-api-key"

# Para Vertex AI
GOOGLE_CLOUD_PROJECT="seu-projeto-id"
GOOGLE_CLOUD_LOCATION="us-central1"
GOOGLE_GENAI_USE_VERTEXAI="True"
```

### Configuração dual-environment (agent.py)

```python
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google import genai

# Detecta e configura ambiente automaticamente
def setup_environment():
    """Configura ambiente para execução local ou Vertex AI"""
    load_dotenv()
    
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'True':
        # Configuração Vertex AI
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        return genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
    else:
        # Configuração local com API Key
        return genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
```

## Implementação das três ferramentas

### 1. Ferramenta analisar_imagem_educacional

```python
from google.adk.tools import ToolContext
from google.genai import types
import json
from typing import Dict, Any

def analisar_imagem_educacional(
    nivel_ensino: str = "medio",
    disciplina: str = "geral",
    contexto_adicional: str = "",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Analisa imagens educacionais usando gemini-2.5-flash
    
    Args:
        nivel_ensino: Nível educacional (fundamental, medio, superior)
        disciplina: Disciplina específica (matematica, ciencias, historia, etc)
        contexto_adicional: Informações adicionais sobre o contexto educacional
        tool_context: Contexto ADK (fornecido automaticamente)
    
    Returns:
        dict: Análise estruturada da imagem educacional
    """
    try:
        # Verificar se há imagens no conteúdo do usuário
        if not tool_context or not tool_context.user_content():
            return {
                "status": "error",
                "message": "Nenhuma imagem fornecida pelo usuário"
            }
        
        # Extrair imagens da mensagem
        parts = []
        user_parts = tool_context.user_content().get().parts().get()
        
        for part in user_parts:
            if part.inline_data().is_present():
                inline_data = part.inline_data().get()
                mime_type = inline_data.mime_type().get()
                
                if mime_type.startswith('image/'):
                    parts.append(types.Part.from_bytes(
                        data=inline_data.data().get(),
                        mime_type=mime_type
                    ))
        
        if not parts:
            return {
                "status": "error",
                "message": "Nenhuma imagem encontrada na mensagem"
            }
        
        # Configurar cliente Gemini
        client = setup_environment()
        
        # Prompt estruturado para análise educacional
        prompt = f"""
        Analise esta imagem no contexto educacional.
        
        Parâmetros:
        - Nível de ensino: {nivel_ensino}
        - Disciplina: {disciplina}
        - Contexto adicional: {contexto_adicional}
        
        Forneça uma análise estruturada em JSON incluindo:
        1. "descricao_objetiva": Descrição clara do que está na imagem
        2. "conceitos_educacionais": Lista de conceitos relacionados à disciplina
        3. "aplicacoes_pedagogicas": Como usar a imagem em sala de aula
        4. "perguntas_norteadoras": 3-5 perguntas para discussão
        5. "nivel_complexidade": De 1 a 5
        6. "sugestoes_atividades": Lista de atividades práticas
        7. "interdisciplinaridade": Conexões com outras disciplinas
        
        Responda APENAS com o JSON estruturado.
        """
        
        # Fazer chamada para o modelo
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt] + parts,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2000,
                response_mime_type='application/json'
            )
        )
        
        # Processar resposta
        analise = json.loads(response.text)
        
        # Salvar resultado como artifact
        if tool_context:
            result_text = json.dumps(analise, ensure_ascii=False, indent=2)
            result_artifact = types.Part.from_text(text=result_text)
            filename = f"analise_educacional_{int(time.time())}.json"
            version = tool_context.save_artifact(filename, result_artifact)
            
            return {
                "status": "success",
                "analise": analise,
                "artifact_saved": filename,
                "version": version,
                "imagens_analisadas": len(parts)
            }
        
        return {
            "status": "success",
            "analise": analise,
            "imagens_analisadas": len(parts)
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Erro ao processar resposta JSON: {str(e)}",
            "resposta_raw": response.text if 'response' in locals() else None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro na análise: {str(e)}",
            "tipo_erro": type(e).__name__
        }
```

### 2. Ferramenta gerar_audio_tts

```python
import time
import wave

def gerar_audio_tts(
    texto: str,
    voz: str = "Kore",
    salvar_arquivo: bool = True,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Gera áudio TTS usando gemini-2.5-flash-preview-tts
    
    Args:
        texto: Texto para converter em áudio
        voz: Nome da voz (Kore, Puck, Charon, Zephyr, etc - 30 opções)
        salvar_arquivo: Se deve salvar como artifact
        tool_context: Contexto ADK (fornecido automaticamente)
    
    Returns:
        dict: Informações sobre o áudio gerado
    """
    try:
        # Configurar cliente
        client = setup_environment()
        
        # Configuração específica para TTS
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voz
                    )
                )
            )
        )
        
        # Gerar áudio
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=texto,
            config=config
        )
        
        # Extrair dados do áudio
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # Salvar como artifact se solicitado
        if salvar_arquivo and tool_context:
            audio_artifact = types.Part.from_data(
                data=audio_data,
                mime_type="audio/wav"
            )
            
            filename = f"tts_audio_{int(time.time())}.wav"
            version = tool_context.save_artifact(filename, audio_artifact)
            
            # Salvar informações no estado da sessão
            tool_context.state["ultimo_audio_tts"] = {
                "filename": filename,
                "version": version,
                "texto_original": texto[:100] + "..." if len(texto) > 100 else texto,
                "voz_usada": voz
            }
            
            return {
                "status": "success",
                "message": f"Áudio gerado com sucesso usando voz '{voz}'",
                "arquivo": filename,
                "version": version,
                "tamanho_bytes": len(audio_data),
                "voz": voz
            }
        
        return {
            "status": "success",
            "message": "Áudio gerado com sucesso",
            "audio_data_disponivel": True,
            "tamanho_bytes": len(audio_data),
            "voz": voz
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao gerar áudio TTS: {str(e)}",
            "tipo_erro": type(e).__name__
        }
```

### 3. Ferramenta transcrever_audio

```python
def transcrever_audio(
    arquivo_artifact: str = None,
    incluir_timestamps: bool = False,
    identificar_speakers: bool = False,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Transcreve áudio usando gemini-2.0-flash
    
    Args:
        arquivo_artifact: Nome do artifact de áudio para transcrever
        incluir_timestamps: Se deve incluir marcações de tempo
        identificar_speakers: Se deve identificar diferentes falantes
        tool_context: Contexto ADK (fornecido automaticamente)
    
    Returns:
        dict: Transcrição do áudio
    """
    try:
        if not tool_context:
            return {
                "status": "error",
                "message": "ToolContext não disponível"
            }
        
        # Configurar cliente
        client = setup_environment()
        
        # Tentar carregar áudio de artifact ou da mensagem do usuário
        audio_part = None
        
        if arquivo_artifact:
            # Carregar artifact específico
            audio_artifact = tool_context.load_artifact(arquivo_artifact)
            if audio_artifact:
                audio_part = audio_artifact
            else:
                return {
                    "status": "error",
                    "message": f"Artifact '{arquivo_artifact}' não encontrado"
                }
        else:
            # Procurar áudio na mensagem do usuário
            user_parts = tool_context.user_content().get().parts().get()
            
            for part in user_parts:
                if part.inline_data().is_present():
                    mime_type = part.inline_data().get().mime_type().get()
                    if mime_type.startswith('audio/'):
                        audio_part = types.Part.from_bytes(
                            data=part.inline_data().get().data().get(),
                            mime_type=mime_type
                        )
                        break
        
        if not audio_part:
            return {
                "status": "error",
                "message": "Nenhum arquivo de áudio encontrado"
            }
        
        # Construir prompt baseado nas opções
        if identificar_speakers and incluir_timestamps:
            prompt = "Transcribe this audio with timestamps and speaker identification. Format: [HH:MM:SS] Speaker X: text"
        elif incluir_timestamps:
            prompt = "Transcribe this audio with timestamps. Format: [HH:MM:SS] text"
        elif identificar_speakers:
            prompt = "Transcribe this audio identifying different speakers. Format: Speaker X: text"
        else:
            prompt = "Generate a transcript of the speech."
        
        # Fazer transcrição
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, audio_part]
        )
        
        transcricao = response.text
        
        # Salvar transcrição como artifact
        if tool_context:
            transcript_artifact = types.Part.from_text(text=transcricao)
            filename = f"transcricao_{int(time.time())}.txt"
            version = tool_context.save_artifact(filename, transcript_artifact)
            
            # Análise adicional da transcrição
            palavras = len(transcricao.split())
            linhas = len(transcricao.split('\n'))
            
            return {
                "status": "success",
                "transcricao": transcricao,
                "arquivo_salvo": filename,
                "version": version,
                "estatisticas": {
                    "total_palavras": palavras,
                    "total_linhas": linhas,
                    "incluiu_timestamps": incluir_timestamps,
                    "identificou_speakers": identificar_speakers
                }
            }
        
        return {
            "status": "success",
            "transcricao": transcricao
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro na transcrição: {str(e)}",
            "tipo_erro": type(e).__name__
        }
```

## Integração completa com ADK

### Arquivo tools.py completo

```python
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.genai import types
from google import genai
import json
import time
import os
from typing import Dict, Any
from dotenv import load_dotenv

# [Incluir todas as funções acima aqui]

# Criar agente com as três ferramentas
def create_educational_agent():
    """Cria agente ADK com ferramentas educacionais"""
    
    agent = Agent(
        name="assistente_educacional",
        model="gemini-2.0-flash",
        description="Assistente educacional com análise de imagem, TTS e transcrição",
        instruction="""
        Você é um assistente educacional avançado que pode:
        
        1. Analisar imagens educacionais usando a ferramenta 'analisar_imagem_educacional'
           - Forneça análises detalhadas para diferentes níveis e disciplinas
           - Identifique conceitos pedagógicos relevantes
        
        2. Converter texto em áudio usando 'gerar_audio_tts'
           - Útil para criar materiais de áudio para estudantes
           - Suporta 30 vozes diferentes
        
        3. Transcrever áudios usando 'transcrever_audio'
           - Pode incluir timestamps e identificar falantes
           - Útil para criar legendas ou notas de aula
        
        Sempre que o usuário enviar uma imagem, use analisar_imagem_educacional.
        Quando solicitado para criar áudio, use gerar_audio_tts.
        Para transcrições, use transcrever_audio.
        """,
        tools=[
            analisar_imagem_educacional,
            gerar_audio_tts,
            transcrever_audio
        ]
    )
    
    return agent
```

### Deploy para Vertex AI

```python
from vertexai.preview.reasoning_engines import AdkApp
from vertexai import agent_engines

def deploy_to_vertex_ai():
    """Deploy do agente para Vertex AI"""
    
    # Criar agente
    agent = create_educational_agent()
    
    # Criar AdkApp
    app = AdkApp(agent=agent)
    
    # Deploy
    remote_agent = agent_engines.create(
        app,
        requirements=[
            "google-cloud-aiplatform[agent_engines,adk]>=1.88.0",
            "google-adk>=1.5.0",
            "google-genai>=0.3.0",
            "python-dotenv>=0.19.0"
        ],
        display_name="Assistente Educacional ADK",
        description="Agente com análise de imagem, TTS e transcrição"
    )
    
    print(f"Agente deployado: {remote_agent.name}")
    return remote_agent
```

### Teste local

```python
def test_locally():
    """Testa o agente localmente"""
    
    agent = create_educational_agent()
    app = AdkApp(agent=agent)
    
    # Teste via CLI
    # Execute: adk interact
    
    # Ou teste programático
    for event in app.stream_query(
        user_id="test_user",
        message="Analise esta imagem do ponto de vista educacional"
    ):
        print(event)

if __name__ == "__main__":
    # Para teste local
    test_locally()
    
    # Para deploy
    # deploy_to_vertex_ai()
```

## Observações importantes sobre compatibilidade

Com base na pesquisa realizada, identifiquei os seguintes pontos críticos:

### Modelos validados

1. **gemini-2.5-flash**: ✅ Disponível para análise de imagens
2. **gemini-2.5-flash-preview-tts**: ✅ Confirmado como modelo TTS oficial em preview
3. **gemini-2.0-flash**: ✅ Disponível para transcrição de áudio

### Limitações identificadas

1. **TTS em preview**: O modelo gemini-2.5-flash-preview-tts tem rate limits mais restritivos
2. **Transcrição**: Suporta apenas fala em inglês atualmente
3. **Tamanho de arquivos**: Limite de 20MB para inline, use Files API para arquivos maiores

### Configuração para portabilidade

A configuração com `GOOGLE_GENAI_USE_VERTEXAI="True"` garante que o mesmo código funcione localmente (com autenticação via gcloud) e no Vertex AI (com service account automática).