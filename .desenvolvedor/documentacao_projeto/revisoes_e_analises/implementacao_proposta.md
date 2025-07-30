# Implementação das Ferramentas com Integração de APIs (Produção)

As ferramentas do **Professor Virtual** foram atualizadas para substituir o comportamento simulado por integrações reais com serviços do Google Cloud, seguindo o **ADK (Agent Development Kit)**. Essas implementações utilizam o sistema de **artifacts** do ADK para manipular arquivos de imagem e áudio de forma eficiente – ou seja, os dados binários são armazenados no contexto da sessão e referenciados por nome, em vez de trafegar diretamente nas mensagens de texto. Abaixo detalhamos cada ferramenta com suas respectivas implementações de produção, conforme recomendado nos comentários do código original (onde se sugeria integrar com serviços reais de STT, Visão e TTS).

## Ferramenta de Transcrição de Áudio (`transcrever_audio`)

**O que foi implementado:** Em vez de retornar texto fixo simulado, esta função agora utiliza a API do **Google Cloud Speech-to-Text** para transcrever o conteúdo do artifact de áudio fornecido. A função obtém os bytes do áudio salvo na sessão através do `tool_context.session.get_artifact`, verifica formato e tamanho, e então configura a requisição para a API de reconhecimento de voz. O áudio é enviado para transcrição e o texto resultante é retornado junto com metadados (duração estimada, formato, tamanho, idioma). Caso ocorra alguma falha (e.g. artifact não encontrado ou erro na API), uma mensagem de erro é retornada.

**Detalhes importantes:**

* **Recuperação do artifact:** Usa `tool_context.session.get_artifact(nome)` para obter os bytes do áudio. Se não existir, retorna erro informando que o artifact não foi encontrado.
* **Validação de formato e tamanho:** São suportados formatos comuns (`wav`, `mp3`, `m4a`) com limite de 10 MB, igual ao código original. Se o formato não for suportado ou o arquivo for muito grande, a função retorna erro apropriado.
* **Chamada à API Speech-to-Text:** A função instancia um cliente do Speech-to-Text e envia os bytes do áudio para transcrição. O `RecognitionConfig` é ajustado para o idioma português do Brasil (`pt-BR`) e para o formato de áudio detectado (por exemplo, define `AudioEncoding.MP3` se for MP3; WAV com PCM é detectado automaticamente pela API).
* **Processamento da resposta:** Se a API retorna resultados, extraímos a transcrição principal. Mantemos o cálculo de `duracao_segundos` como no código original (estimativa baseada em 16 kHz mono) apenas para fornecer um valor aproximado. Em produção, poderíamos calcular a duração com base no cabeçalho do arquivo de áudio para maior precisão.
* **Resultado:** Retorna um dicionário com `sucesso=True`, o `texto` transcrito, e metadados como duração, formato, tamanho em bytes e idioma. Isso mantém compatibilidade com o formato de resposta esperado pelo restante do sistema.

**Código da ferramenta `transcrever_audio.py`:**

```python
"""Ferramenta para transcrever áudio para texto (integração com Google STT)."""

from typing import Dict, Any
from google.adk.tools import ToolContext

# Import da biblioteca do Google Cloud Speech-to-Text
from google.cloud import speech

def transcrever_audio(nome_artefato_audio: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Transcreve um artifact de áudio para texto usando a API Google Speech-to-Text."""
    try:
        # 1. Recuperar o artifact de áudio da sessão
        artifact = tool_context.session.get_artifact(nome_artefato_audio)
        if not artifact:
            return {
                "erro": f"Artefato de áudio '{nome_artefato_audio}' não encontrado na sessão.",
                "sucesso": False
            }
        audio_bytes = artifact.content
        formato = artifact.name.split('.')[-1].lower() if '.' in artifact.name else "desconhecido"

        # 2. Validações de formato e tamanho
        formatos_suportados = ["wav", "mp3", "m4a"]
        if formato not in formatos_suportados:
            return {"erro": f"Formato '{formato}' não suportado", "sucesso": False}
        if len(audio_bytes) > 10 * 1024 * 1024:  # 10MB
            return {"erro": "Arquivo de áudio muito grande (máximo 10MB)", "sucesso": False}

        # 3. Configurar e chamar a API de Speech-to-Text do Google
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_bytes)
        # Define as configurações de acordo com o formato e idioma
        config_params = {"language_code": "pt-BR"}
        if formato == "mp3" or formato == "m4a":
            config_params["encoding"] = speech.RecognitionConfig.AudioEncoding.MP3
        elif formato == "wav":
            config_params["encoding"] = speech.RecognitionConfig.AudioEncoding.LINEAR16
            # Opcional: poderíamos extrair sample rate do WAV se necessário
        config = speech.RecognitionConfig(**config_params)
        response = client.recognize(config=config, audio=audio)

        # 4. Processar a resposta da API
        if not response.results:
            return {"erro": "Falha no reconhecimento de fala (nenhum resultado)", "sucesso": False}
        transcript = response.results[0].alternatives[0].transcript

        # 5. Calcular duração aproximada (segundos) - assumindo áudio 16 kHz mono
        duracao_segundos = len(audio_bytes) / (16000 * 2)

        return {
            "sucesso": True,
            "texto": transcript,
            "duracao_segundos": duracao_segundos,
            "formato": formato,
            "tamanho_bytes": len(audio_bytes),
            "idioma_detectado": "pt-BR"
        }
    except Exception as e:
        return {
            "erro": f"Erro ao transcrever áudio: {str(e)}",
            "sucesso": False
        }
```

*Observação:* Certifique-se de que as credenciais e permissões para uso da API de Speech-to-Text estejam configuradas (por exemplo, variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS`). A integração acima segue as recomendações do código original, substituindo o texto simulado por uma chamada real ao serviço de STT.

## Ferramenta de Geração de Áudio TTS (`gerar_audio_tts`)

**O que foi implementado:** A função de TTS agora utiliza a API do **Google Cloud Text-to-Speech** para converter texto em fala. Originalmente, o código apenas gerava bytes simulados; agora fazemos uma chamada real ao serviço de TTS, obtendo dados de áudio (formato MP3) correspondentes ao texto de entrada. O áudio resultante é então armazenado como um artifact na sessão (em vez de retorná-lo diretamente), de modo que o front-end ou outras partes do agente possam recuperá-lo pelo nome do arquivo gerado. Isso aproveita o mecanismo de artifacts do ADK para lidar com o binário do áudio de forma transparente.

**Detalhes importantes:**

* **Verificação do texto de entrada:** Se a string estiver vazia ou em branco, retornamos um erro indicando que nenhum texto foi fornecido (prevenindo chamadas desnecessárias à API).
* **Chamada à API Text-to-Speech:** A função configura o cliente do TTS com o idioma/voz desejados. Usamos por padrão a voz **“pt-BR-Standard-A”** (conforme parâmetro padrão `voz`), mas isso pode ser customizado. Também utilizamos o parâmetro `velocidade` para ajustar a velocidade da fala (1.0 = normal). O áudio é solicitado no formato **MP3** para consistência.
* **Criação do artifact de áudio:** Recebido o `audio_content` (bytes do MP3) da resposta da API, criamos um nome de arquivo único para o artifact (usando `uuid.uuid4()` para evitar colisões) com extensão `.mp3`. Em seguida, utilizamos `tool_context.session.create_artifact` para salvar esses bytes no contexto da sessão com o MIME type apropriado. Isso registra o artifact no *ArtifactService* do ADK, permitindo seu acesso posterior pelo nome gerado.
* **Resultado:** A função retorna um dicionário com `sucesso=True` e o nome do artifact gerado (`nome_artefato_gerado`), além de um campo informativo `tamanho_caracteres` (quantidade de caracteres do texto original). Caso ocorra alguma exceção, retorna-se um erro com mensagem detalhada.

**Código da ferramenta `gerar_audio_tts.py`:**

```python
"""Ferramenta para gerar um artifact de áudio TTS a partir de texto (integração com Google TTS)."""

import uuid
from typing import Dict, Any
from google.adk.tools import ToolContext

# Import da biblioteca do Google Cloud Text-to-Speech
from google.cloud import texttospeech

def gerar_audio_tts(texto: str, tool_context: ToolContext, velocidade: float = 1.0, voz: str = "pt-BR-Standard-A") -> Dict[str, Any]:
    """Gera um artifact de áudio (MP3) a partir de um texto usando a API Google Text-to-Speech."""
    try:
        # 1. Validação da entrada
        if not texto or len(texto.strip()) == 0:
            return {"erro": "Texto vazio fornecido", "sucesso": False}

        # 2. Configurar a chamada para a API de TTS
        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(text=texto)
        # Define a voz (idioma e variante) e as configurações de áudio
        voice_params = texttospeech.VoiceSelectionParams(language_code="pt-BR", name=voz)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=velocidade
        )

        # 3. Requisitar síntese de fala à API
        response = client.synthesize_speech(request={"input": input_text, "voice": voice_params, "audio_config": audio_config})
        audio_bytes = response.audio_content  # bytes do áudio MP3 gerado

        # 4. Salvar o áudio gerado como um artifact na sessão
        nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
        tool_context.session.create_artifact(name=nome_artefato, content=audio_bytes, mime_type="audio/mpeg")

        # 5. Retornar o nome do artifact para referência
        return {
            "sucesso": True,
            "nome_artefato_gerado": nome_artefato,
            "tamanho_caracteres": len(texto)
        }
    except Exception as e:
        return {
            "erro": f"Erro ao gerar áudio TTS: {str(e)}",
            "sucesso": False
        }
```

Como recomendado no código base, substituímos os bytes simulados por uma integração real com a API de TTS do Google. O uso de artifacts garante que o áudio gerado possa ser acessado via nome (e.g. pelo front-end ou outras ferramentas), em vez de inserir um payload binário na resposta do agente. Basta que o sistema cliente saiba o `nome_artefato_gerado` para então carregar ou fazer o download desse áudio através do ADK.

## Ferramenta de Análise de Imagem Educacional (`analisar_imagem_educacional`)

**O que foi implementado:** Esta ferramenta agora integra com a API do **Google Cloud Vision** para extrair informações da imagem enviada pelo estudante. Originalmente, ela devolvia sempre um resultado fixo indicando presença de uma equação quadrática e um gráfico; agora a análise considera de forma dinâmica o conteúdo da imagem, incluindo texto detectado e características visuais, para inferir o contexto educacional. Em resumo, fazemos uma detecção de texto (OCR) na imagem e, com base no texto encontrado ou em labels da imagem, definimos: o tipo de conteúdo (por ex. exercício de matemática, texto, diagrama), elementos detectados (ex: "equação", "gráfico"), o contexto educacional (por ex. "Exercício de matemática sobre ..."), além de avaliar a qualidade da imagem.

**Detalhes importantes:**

* **Recuperação do artifact de imagem:** A função usa `tool_context.session.get_artifact` para obter os bytes da imagem através do nome fornecido. Se o artifact não existir na sessão, retorna erro informando isso.
* **Validação de tamanho:** Limite de 5 MB para a imagem, conforme o código original. Imagens maiores retornam erro imediatamente para evitar processamento pesado.
* **Chamada à API Cloud Vision (OCR e análise):** Utilizamos o client do Vision (`ImageAnnotatorClient`) para realizar a detecção de texto na imagem (`text_detection`).

  * Se algum texto é encontrado na imagem, ele é extraído para análise. Com base nesse texto, fazemos heurísticas simples: se há números, fórmulas ou o símbolo “=” nas strings detectadas, inferimos que se trata de um **exercício de matemática**. Palavras indicando enunciados educacionais podem ser usadas para determinar o tipo de conteúdo (por exemplo, presença de muitas palavras sem fórmulas poderia indicar um texto narrativo ou teórico em vez de um exercício matemático).
  * **Elementos detectados:** Também a partir do texto (e possivelmente da estrutura dele), identificamos elementos específicos. No código abaixo, como exemplo, se encontramos padrões de uma equação quadrática (e.g. `x^2` ou `x²`), adicionamos `"equação quadrática"` à lista de elementos. Poderíamos expandir isso para identificar gráficos mencionados no texto (ex.: palavra "gráfico" ou "figura") ou outros elementos relevantes.
  * Se **nenhum texto** for encontrado via OCR (por exemplo, a imagem pode ser puramente um gráfico ou diagrama sem texto legível), recorremos a **label detection** (detecção de rótulos) para obter descrições visuais gerais da imagem. Com isso, podemos inferir se é um diagrama, um gráfico etc. (por exemplo, se aparecerem labels como "diagram" ou "chart").
* **Inferência do contexto educacional:** Combinando os passos acima, definimos campos descritivos:

  * `tipo_conteudo`: uma classificação simples do tipo de mídia educacional. Exemplos: `"exercicio_matematica"`, `"texto_educacional"`, `"diagrama"`, etc., dependendo do caso.
  * `elementos_detectados`: lista de itens de interesse encontrados (palavras-chave como "equação", "gráfico", "tabela", etc.).
  * `contexto_educacional`: uma frase descrevendo em alto nível do que se trata o conteúdo da imagem. No exemplo implementado, se detectamos uma equação quadrática, definimos *"Exercício de matemática sobre funções quadráticas"* (semelhante ao exemplo fornecido originalmente).
* **Qualidade da imagem:** Mantivemos a lógica do código original: se a imagem for muito pequena (aqui usamos `< 10000` bytes como heurística de baixa resolução), marcamos `qualidade_adequada=False` e sugerimos uma ação (e.g. *"Imagem pode estar com baixa resolução"*). Em produção, seria preferível inspecionar de fato as dimensões (pixel width/height) ou resolução da imagem para julgar qualidade, mas usamos o critério simples do tamanho em bytes conforme o original.
* **Resultado:** Retorna um dicionário com `sucesso=True` contendo todos os campos acima (`tipo_conteudo`, `elementos_detectados`, `contexto_educacional`, `qualidade_adequada`, `sugestao_acao`, `tamanho_bytes` e repete o `contexto_pergunta` fornecido). Em caso de erro (artifact não encontrado ou exceção durante análise), retorna `sucesso=False` com mensagem de erro.

**Código da ferramenta `analisar_imagem_educacional.py`:**

```python
"""Ferramenta para extrair informações educacionais relevantes de uma imagem (integração com Google Vision API)."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from google.adk.tools import ToolContext

# Import da biblioteca do Google Cloud Vision
from google.cloud import vision

@dataclass
class AnaliseImagemResult:
    """Resultado da análise de imagem educacional."""
    tipo_conteudo: str
    elementos_detectados: list[str]
    contexto_educacional: str
    qualidade_adequada: bool
    sugestao_acao: Optional[str]

def analisar_imagem_educacional(nome_artefato_imagem: str, contexto_pergunta: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Extrai informações educacionais relevantes de uma imagem usando a API Google Vision."""
    try:
        # 1. Obter o artifact de imagem da sessão
        artifact = tool_context.session.get_artifact(nome_artefato_imagem)
        if not artifact:
            return {
                "erro": f"Artefato de imagem '{nome_artefato_imagem}' não encontrado.",
                "sucesso": False,
                "qualidade_adequada": False
            }
        imagem_bytes = artifact.content

        # 2. Validação de tamanho da imagem
        if len(imagem_bytes) > 5 * 1024 * 1024:  # 5MB
            return {
                "erro": "Imagem muito grande (máximo 5MB)",
                "sucesso": False,
                "qualidade_adequada": False
            }

        # 3. Análise do conteúdo da imagem usando Google Vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=imagem_bytes)
        resultado_tipo = "desconhecido"
        elementos = []
        contexto = ""

        # 3a. Tentativa de OCR (detecção de texto na imagem)
        ocr_response = client.text_detection(image=image)
        texto_detectado = ""
        if ocr_response.text_annotations:
            texto_detectado = ocr_response.text_annotations[0].description  # texto completo detectado
        if texto_detectado:
            # Normalizar texto para análise (minúsculas, sem acentos idealmente)
            texto_lower = texto_detectado.lower()
            # Inferir tipo de conteúdo baseado no texto
            if any(char.isdigit() for char in texto_lower) or "=" in texto_lower:
                resultado_tipo = "exercicio_matematica"
            else:
                resultado_tipo = "texto_educacional"
            # Identificar elementos específicos no texto (exemplos simples)
            if "=" in texto_lower:
                elementos.append("equação matemática")
                # Verificar se parece equação quadrática (x^2 ou x² presente)
                if "x^2" in texto_lower or "x²" in texto_lower:
                    elementos.append("equação quadrática")
            # (Outros elementos podem ser adicionados aqui, ex: detectar "figura", "gráfico" no texto)
        else:
            # 3b. Se nenhum texto encontrado, tentar detecção de labels (conteúdo visual)
            label_response = client.label_detection(image=image)
            labels = [label.description.lower() for label in label_response.label_annotations]
            if any(term in labels for term in ["diagram", "chart", "graph"]):
                resultado_tipo = "diagrama"
                elementos.append("gráfico/diagrama")
            else:
                resultado_tipo = "imagem"

        # 3c. Definir contexto educacional baseando-se no tipo e elementos
        if resultado_tipo == "exercicio_matematica":
            contexto = "Exercício de matemática"
            if "equação quadrática" in elementos:
                contexto = "Exercício de matemática sobre funções quadráticas"
        elif resultado_tipo == "texto_educacional":
            contexto = "Texto educacional (conteúdo teórico ou explicativo)"
        elif resultado_tipo == "diagrama":
            contexto = "Diagrama ou gráfico relacionado ao conteúdo educacional"
        else:
            contexto = "Imagem educacional (conteúdo visual)"

        # 4. Avaliação simples de qualidade da imagem
        qualidade = True
        sugestao = None
        if len(imagem_bytes) < 10000:  # muito pequena em bytes, possivelmente baixa resolução
            qualidade = False
            sugestao = "Imagem pode estar com baixa resolução"

        # 5. Montar resultado
        resultado = {
            "sucesso": True,
            "tipo_conteudo": resultado_tipo,
            "elementos_detectados": elementos,
            "contexto_educacional": contexto,
            "qualidade_adequada": qualidade,
            "sugestao_acao": sugestao,
            "tamanho_bytes": len(imagem_bytes),
            "contexto_pergunta": contexto_pergunta
        }
        return resultado
    except Exception as e:
        return {
            "erro": f"Erro ao analisar imagem: {str(e)}",
            "sucesso": False,
            "qualidade_adequada": False
        }
```

Conforme indicado previamente no código documentado, integrando um serviço real de visão computacional podemos extrair informações relevantes da imagem em vez de usar valores fixos. A implementação acima pode ser aprimorada com regras adicionais dependendo das necessidades (por exemplo, reconhecer gráficos de outros tipos, identificar texto manuscrito, etc.), mas já demonstra o uso da **Cloud Vision API** para obter texto e labels. Importante destacar que manter o uso de artifacts significa que a imagem foi fornecida ao agente (por upload do usuário, possivelmente) e está armazenada no *ArtifactService* do ADK – o agente acessa esses bytes pelo nome, analisa-os, e **não precisa inserir os bytes brutos ou resultado extenso diretamente na mensagem**.

---

**Conclusão:** As três ferramentas agora estão implementadas de forma compatível com o ADK e as APIs do Google Cloud, seguindo os padrões de artifacts e as recomendações do projeto. Cada ferramenta busca seus inputs binários via *Artifacts*, realiza a operação necessária usando um serviço externo (STT, TTS ou Vision) e retorna resultados estruturados. Dessa forma, o agente **Professor Virtual** pode funcionar em produção, fornecendo transcrição de perguntas de áudio, análise de imagens educacionais e respostas em áudio geradas de forma confiável e escalável, conforme esperado.&#x20;
