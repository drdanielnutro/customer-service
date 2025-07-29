# Validação do Relatório de Correções – Sistema de Artifacts do Professor Virtual

## 1. Configurações de Artifact Service em `config.py`

O arquivo de configuração **não contém parâmetros para o serviço de artefatos (artifact\_service)** nem informações do Google Cloud Storage (GCS) na branch atual. Conforme o código atual, as últimas entradas definidas em `Config` são `app_name`, `CLOUD_PROJECT`, `CLOUD_LOCATION`, `GENAI_USE_VERTEXAI` e `API_KEY`, sem qualquer menção a tipo de storage de artifact ou bucket do GCS. Isso confirma a **falta de configurações do artifact\_service e GCS** mencionada no relatório.

A sugestão de adicionar campos como `artifact_storage_type` (definindo “memory” ou “gcs”), `gcs_bucket_name` e um flag `is_production` é coerente. De acordo com a documentação do Google ADK, ao inicializar o Runner do agente deve-se fornecer uma implementação de **ArtifactService** – por exemplo, um serviço em memória para testes ou um serviço persistente no GCS em produção. Incluir essas configurações no `config.py` permite escolher entre armazenar artefatos em memória ou no **Google Cloud Storage**, além de especificar o nome do bucket e controlar via `is_production` quando usar o GCS. Essa alteração alinha o projeto às práticas recomendadas do ADK, garantindo que os artefatos possam ser persistidos adequadamente em ambiente de produção.

## 2. Inicialização do ArtifactService no Runner (`agent.py`)

No código atual do `agent.py`, o agente raiz (`root_agent`) é criado mas **nenhum Runner é instanciado com artifact\_service configurado**. Isso significa que os artefatos não estão sendo gerenciados por um serviço dedicado, o que impede persistência e versionamento adequados. A documentação do ADK enfatiza que, para habilitar o uso de artefatos, **o Runner deve ser iniciado com um ArtifactService** (por exemplo, `InMemoryArtifactService` ou `GcsArtifactService`) além do SessionService.

A correção sugerida – importar `Runner`, `InMemorySessionService`, `InMemoryArtifactService` e `GcsArtifactService`, e criar o Runner passando `artifact_service` configurado – é apropriada. De fato, o *snippet* de exemplo oficial mostra exatamente essa estrutura, inicializando o Runner com um ArtifactService e SessionService. Portanto, substituir o código atual para criar o Runner assim:

```python
artifact_service = GcsArtifactService(...) if (configs.is_production and configs.artifact_storage_type=="gcs") else InMemoryArtifactService()
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=configs.app_name, session_service=session_service, artifact_service=artifact_service)
```

está de acordo com a documentação. Essa mudança garante que **os métodos de artifact (load/save)** passem a funcionar, pois agora há um serviço responsável por armazenar e recuperar os artefatos durante a execução do agente.

## 3. Ferramenta `analisar_imagem_educacional.py` – APIs de Artifact e Assincronismo

**Problema 1 – Uso de `session.get_artifact`:** A implementação atual da ferramenta usa `tool_context.session.get_artifact(nome_artefato)` para obter o artefato da imagem. Contudo, essa chamada **não faz parte da API oficial do ADK** – conforme observado, a documentação oficial define o método correto como `tool_context.load_artifact(filename)` retornando um objeto `types.Part` com os dados. Inclusive, um documento de compatibilidade do próprio projeto reconhece que o código legado usou `get_artifact` por convenção interna, enquanto o ADK oficial recomenda `load_artifact()`. Portanto, a substituição proposta por `artifact = await tool_context.load_artifact(nome_artefato_imagem)` é **necessária e correta**.

**Problema 2 – Função deve ser assíncrona:** A assinatura atual da função é síncrona (`def analisar_imagem_educacional(...)`), mas a chamada à nova API `load_artifact` requer uso de `await`. A partir do ADK v1.0, **todas as operações de serviços centrais tornaram-se assíncronas**, incluindo carregar artefatos. Isso significa que a ferramenta precisa ser `async def` para poder usar `await tool_context.load_artifact(...)`. A mudança para função assíncrona está alinhada com a evolução do ADK e é imprescindível para o código funcionar corretamente no contexto atualizado.

**Problema 3 – Acesso aos dados do artifact:** No código existente, após obter o artifact, acessa-se `artifact.content` diretamente. No ADK, entretanto, o conteúdo binário do artifact vem encapsulado em `artifact.inline_data`. O correto é verificar se o artifact retornado possui `inline_data` e então extrair os bytes e mime type: `imagem_bytes = artifact.inline_data.data` e `mime_type = artifact.inline_data.mime_type`. A documentação descreve que um `types.Part` armazena dados binários dentro de `inline_data` (com campos `data` e `mime_type`). Inclusive, em exemplos oficiais, após o `load_artifact` é comum checar e usar `artifact.inline_data.data` para obter os bytes. Portanto, a modificação sugerida para extrair `imagem_bytes` via `artifact.inline_data.data` e validar sua presença está correta. Isso garante compatibilidade tanto com artefatos em memória quanto persistidos, evitando erros ao acessar um atributo inexistente (`content`).

Em resumo, para essa ferramenta a validação confirma que **as três mudanças propostas (uso de load\_artifact com await, definição como async, e acesso via inline\_data)** estão de acordo com a API atual do ADK e resolvem os problemas identificados.

## 4. Ferramenta `gerar_audio_tts.py` – Salvar Artefato de Áudio

**Problema 1 – Uso de `session.create_artifact`:** No trecho atual, após gerar os bytes de áudio TTS, o código salva o artefato chamando `tool_context.session.create_artifact(name, content=audio_bytes, mime_type="audio/mpeg")`. Essa abordagem não corresponde à API oficial; não existe um método público `create_artifact` na sessão do ADK Python. O procedimento correto é utilizar `tool_context.save_artifact(nome, artifact_part)`, onde `artifact_part` é um objeto `types.Part` contendo os bytes e MIME type do arquivo. A documentação do ADK ilustra esse padrão – primeiro cria-se um `Part` do conteúdo (por exemplo, `types.Part.from_data(data=..., mime_type=...)`), então utiliza-se `await context.save_artifact(filename, artifact)` para persistir. Portanto, substituir a chamada por:

```python
audio_part = types.Part.from_data(data=audio_bytes, mime_type="audio/mpeg")
version = await tool_context.save_artifact(nome_artefato, audio_part)
```

é **correto**. Essa mudança assegura que o artefato de áudio seja salvo através do ArtifactService configurado (em memória ou GCS), seguindo o fluxo suportado pelo ADK.

**Problema 2 – Tornar a função assíncrona:** Similar ao caso anterior, a função `gerar_audio_tts` deve ser declarada com `async def`. Conforme destacado, métodos como `save_artifact` agora são assíncronos e exigem `await`. De fato, no exemplo da própria documentação, após gerar um artifact a função de ferramenta é `async` e executa `version = await context.save_artifact(...)`. Logo, ajustar a definição para assíncrona e usar `await` é necessário para o código funcionar e não bloquear o loop do agente.

**Problema 3 – Incluir versão no retorno:** Atualmente, o retorno dessa ferramenta inclui campos como `nome_artefato_gerado` e tamanhos, mas não informa a versão do artifact salvo. A versão é retornada pelo método `save_artifact` (um inteiro auto-incremental começando em 0). Incluir esse valor no dicionário de resposta (por exemplo, `"versao": version`) é uma boa prática para rastrear qual instância do artefato foi criada. Embora não seja obrigatório, tal dado pode ser útil para debug ou para o frontend saber que um artefato foi salvo com sucesso. Portanto, adicionar `"versao": version` na resposta, conforme sugerido, **faz sentido e está de acordo com o comportamento do ADK**, que fornece o número da versão toda vez que um artifact é salvo.

## 5. Ferramenta `transcrever_audio.py` – Correções de Assincronismo e Artifact

**Problema 1 – Função deve ser assíncrona:** A função `transcrever_audio` atualmente é definida de forma síncrona (`def transcrever_audio(...)`). Entretanto, ela utiliza internamente operações que deveriam ser assíncronas (carregar e salvar artefatos). Conforme a mudança de arquitetura do ADK 1.0, todas essas chamadas precisam ser aguardadas com `await`. Portanto, a função precisa ser marcada como `async def` para suportar o uso de `await` em seu corpo. Essa alteração é consistente com as exigências do ADK e evita erros de execução (por exemplo, tentar usar `await` em uma função não assíncrona gera SyntaxError).

**Problema 2 – Uso de `load_artifact` com await:** No código atual, a obtenção do áudio é feita com `audio_artifact = tool_context.load_artifact(nome_artefato_audio)`, sem `await`. Isso sugere que o artifact possivelmente não está sendo realmente carregado (provavelmente retornando um objeto *awaitable* ou None imediatamente). A correção indicada – `audio_artifact = await tool_context.load_artifact(nome_artefato_audio)` – está em linha com a documentação do ADK, que exemplifica o uso correto desse método com await dentro de funções assíncronas. Com a função convertida para `async`, essa mudança garantirá que o áudio do artifact seja efetivamente recuperado antes de prosseguir.

**Problema 3 – Uso de `save_artifact` com await:** De modo análogo, ao salvar a transcrição gerada, o código atual faz `versao_salva = tool_context.save_artifact(filename, transcript_artifact)` sem aguardar. O correto é `versao_salva = await tool_context.save_artifact(filename, transcript_artifact)`, conforme o padrão do ADK. Isso assegura que o artifact de texto da transcrição seja salvo no serviço de artefatos e retorne a versão criada. A ausência do await poderia levar a não salvar nada ou retornar um objeto incompleto. Portanto, essa modificação é necessária e coerente com as práticas do ADK.

**Problema 4 – Função auxiliar `_buscar_audio_na_mensagem` assíncrona:** A função `_buscar_audio_na_mensagem`, que tenta obter um artifact de áudio diretamente do conteúdo da mensagem do usuário, atualmente é síncrona. Se tornarmos `transcrever_audio` assíncrona, qualquer chamada a `_buscar_audio_na_mensagem` dentro dela precisará ser com `await`. Por isso, faz sentido transformar também `_buscar_audio_na_mensagem` em `async def`. Dessa forma, no ponto de uso (`audio_artifact = await _buscar_audio_na_mensagem(tool_context)`) a chamada passa a ser válida. Essa função auxiliar em si provavelmente faz operações rápidas (inspeção do `tool_context.user_content()`), que não necessariamente exigem await; porém, para manter a consistência do fluxo assíncrono e permitir a chamada correta, é recomendável ajustá-la conforme sugerido.

Em suma, todas as correções propostas para `transcrever_audio.py` – tornar as funções `async`, inserir awaits em `load_artifact`/`save_artifact` e ajustar a função auxiliar – **são validadas pela documentação e pelas mudanças de breaking change do ADK v1.0+**. Isso resolverá problemas de artifacts não carregarem corretamente e evitará comportamentos inesperados de concorrência.

## 6. Novo Módulo `artifact_handler.py` – Upload de Arquivos do Frontend

A criação de um novo arquivo `artifact_handler.py` para lidar com uploads de arquivos do frontend é coerente com a arquitetura ADK. Atualmente, não existe um handler dedicado para isso no projeto (nenhum `handle_file_upload` foi encontrado no repositório). A proposta é implementar uma função async `handle_file_upload(file_data, context)` que:

* Decodifica o conteúdo base64 recebido do front (ou usa diretamente bytes, caso já estejam em bytes).
* Cria um objeto `types.Part` a partir desses bytes com o MIME type fornecido (usando `types.Part.from_data`).
* Usa `await context.save_artifact(filename, artifact)` para salvar o arquivo no ArtifactService configurado, obtendo a versão gerada.
* Retorna um dicionário indicando sucesso, com nome do arquivo salvo, versão e tamanho em bytes.

Essa solução segue a lógica esperada. A documentação do ADK apresenta padrões semelhantes para receber dados binários externos e salvá-los como artifacts via contextos de invocação/callback. No exemplo oficial, um conjunto de bytes (`report_bytes`) é encapsulado em um `Part` e salvo com `save_artifact`, dentro de uma função async que atua como **callback/handler** de um evento. O handler sugerido utiliza `InvocationContext` como contexto – que é compatível com as chamadas de save\_artifact fora do escopo de uma ferramenta específica (por exemplo, em uma rota de API separada). Tudo indica que essa implementação permitirá que o backend crie explicitamente um artifact quando o frontend enviar um arquivo, **em vez de depender de um upload implícito pelo ADK Web UI**.

Não há indícios de contradição: decodificar base64 e salvar via ArtifactService é a abordagem correta quando o front não utiliza diretamente um SDK para upload. Essa função servirá de ponte entre o aplicativo Flutter (que envia JSON com o arquivo codificado) e o mecanismo de artifacts do ADK.

## 7. Orientações para Modificações no Frontend (Flutter)

As recomendações listadas para o frontend estão em conformidade com o funcionamento esperado do ADK e boas práticas de envio de arquivos:

* **Formato de envio:** O frontend deve enviar um JSON contendo a ação `"upload_file"` e os dados do arquivo (`file_data`) com campos `content` (base64 do arquivo), `mime_type` apropriado e `filename`. Esse formato explícito garante que o backend saiba tratar a requisição como um upload. De fato, o ADK suporta o conceito de **user uploads** integrados, mas como não há SDK específico para Flutter, faz-se necessário esse contrato manual. A documentação cita que usuários podem enviar arquivos para serem tratados como artifacts, e essa solução implementa exatamente isso de forma transparente via JSON.

* **Nada de arquivos binários brutos no corpo:** Enviar o conteúdo binário puro poderia causar problemas (por exemplo, quebra de protocolo JSON ou encoding). Por isso a conversão para base64 no app cliente é obrigatória. Base64 encapsula binários em texto, seguro para JSON.

* **Não esperar mágicas do Runner:** O Runner do ADK não cria artifacts automaticamente a partir de uploads arbitrários a menos que esses sejam enviados através da interface web padrão com ArtifactService habilitado. No caso de uso via API, é correto **não contar com comportamento automático**, mas sim utilizar o handler no backend para criar o artifact (como implementado em `artifact_handler.py`). Também não é possível usar diretamente chamadas ADK no app Flutter (pois não há uma biblioteca cliente ADK pronta), então essa estratégia custom é necessária.

* **Confirmar sucesso com resposta do backend:** O frontend deve aguardar o retorno do backend com o nome e versão do artifact salvo, indicando sucesso. Isso segue o fluxo normal: primeiro enviar os dados, depois receber uma confirmação. Assim, evita-se condições de corrida em que o front tenta usar um artifact antes de salvo. A inclusão de `version` na resposta do handler auxilia nesse controle.

Em resumo, as instruções dadas ao frontend são sensatas e compatíveis com o design do ADK. Elas garantem que o upload seja feito de forma robusta: **arquivo convertido para base64, enviado via JSON com MIME e nome**, processado no backend (criando artifact), e então confirmado de volta. Essa é a maneira correta de integrar uploads de arquivos de um app cliente externo com o sistema de artifacts do agente.

## Conclusão

Cada ponto levantado no relatório foi confirmado pela análise do código-fonte e da documentação oficial:

* **APIs de Artifact depreciadas/inexistentes:** De fato, o código usava métodos não suportados (`get_artifact`, `create_artifact`), e a mudança para `load_artifact`/`save_artifact` com await é devidamente respaldada.
* **Configuração do ArtifactService:** O projeto carecia dessa configuração e a adição é alinhada com as necessidades do ADK para persistir artefatos.
* **Assincronismo:** Várias funções síncronas precisam ser async. A mudança é mandatória segundo as notas de versão do ADK 1.x e os exemplos de uso de artifacts.
* **GCS em produção:** A estratégia de alternar entre InMemory e GCS via config é consistente com as implementações disponíveis no ADK (InMemoryArtifactService vs GcsArtifactService).
* **Upload explícito pelo frontend:** A solução de codificar o arquivo e usar um handler dedicado no backend é confirmada como o caminho correto, dado que o ADK não fornece SDK Flutter nem faz uploads automáticos fora do ambiente web padrão.

Dessa forma, **as correções propostas no relatório são consideradas adequadas e fundamentadas**. Implementá-las deixará o sistema de artifacts do Professor Virtual em conformidade com a API atual do Google ADK, melhorando a estabilidade e permitindo o funcionamento dos recursos de upload e manipulação de arquivos conforme esperado.

**Fontes:**

1. Trecho do `config.py` sem configs de artifact; Documentação ADK sobre InMemory/GCS ArtifactService.
2. Código atual do `agent.py` (sem Runner configurado); Exemplo de inicialização de Runner com ArtifactService.
3. Código de `analisar_imagem_educacional` usando get\_artifact; Nota de compatibilidade indicando uso de load\_artifact no ADK; Exemplo de load\_artifact e acesso via inline\_data.
4. Código de `gerar_audio_tts` usando create\_artifact; Exemplo de save\_artifact com Part e obtenção de versão.
5. Código de `transcrever_audio` sem awaits; Confirmação do ADK v1.0 sobre necessidade de await em serviços (assíncronos).
6. Padrão sugerido de handler de upload criando artifact.
7. Diretriz de uploads via frontend e uso de artifacts; Discussão sobre processo de carregar e salvar artifact de upload (StackOverflow).


# Validação das Informações Complementares - item 8 em diante do arquivo "correcoes_sugeridas.md"

## Arquitetura de Artifacts no ADK

**Conceitos Fundamentais:**

1. **Artifact:** No contexto do Google ADK (Agent Development Kit), um *artifact* representa um dado binário (como uma imagem ou áudio) identificado por um nome de arquivo único dentro de seu escopo. Esse nome (filename) deve ser único na sessão ou no escopo de usuário correspondente e idealmente incluir extensões descritivas (e.g. `"imagem.png"`, `"audio.wav"`), embora a extensão não influencie a lógica de armazenamento.

2. **Representação:** Internamente, todo artifact é representado como um objeto `google.genai.types.Part` contendo dados *inline* (no campo `inline_data`). Esse objeto *Part* inclui os bytes brutos do arquivo (`data`) e seu tipo MIME (`mime_type`) para que o sistema saiba do que se trata (por exemplo, `"image/png"`, `"audio/mpeg"`, etc.). Essa é a estrutura padrão usada pelo ADK tanto para partes de mensagens de LLM quanto para artifacts persistidos.

3. **Storage:** Os artifacts **não ficam armazenados no estado da sessão ou inseridos diretamente nas mensagens de texto**. Em vez disso, seu armazenamento e recuperação são gerenciados por um serviço dedicado de Artifact (implementações de `BaseArtifactService`) fornecido ao inicializar o *runner* do agente. Em ambientes de produção usando Google Cloud/Vertex AI, tipicamente se configura um `GcsArtifactService` – que usa um bucket no Google Cloud Storage (GCS) – para persistir os artifacts de forma duradoura. (No nosso caso, presume-se um bucket configurado, e.g. `"adk-professor-virtual-artifacts"`, para armazenar os arquivos do **Professor Virtual**). Para testes ou uso temporário, existe também um `InMemoryArtifactService` que guarda os dados apenas em memória durante a execução.

4. **Namespacing (Escopo de sessão vs usuário):** O ADK distingue artifacts por escopo:

   * Por padrão, um artifact salvo com um nome simples (sem prefixo especial) fica **atrelado à sessão atual** do usuário. Ou seja, ele é acessível apenas dentro da combinação daquele `app_name` + `user_id` + `session_id`. Cada sessão do agente tem seu próprio espaço de filenames.
   * Se desejarmos que um artifact seja **persistido entre múltiplas sessões do mesmo usuário**, utilizamos o prefixo especial `"user:"` no nome do arquivo. Por exemplo, `"user:avatar.png"` ficará associado apenas ao `app_name` e `user_id`, independentemente do `session_id`. O ArtifactService reconhece o prefixo `"user:"` e armazena nesse escopo mais amplo, permitindo que qualquer sessão futura do mesmo usuário acesse o mesmo artifact. (Internamente, o caminho de armazenamento usa a palavra-chave `user` no lugar do ID de sessão quando esse prefixo é usado.)

5. **Versionamento:** O ADK implementa versionamento automático de artifacts. Cada vez que um mesmo filename é salvo de novo, o serviço atribui um número de versão incremental. A primeira vez que um artifact é salvo, recebe versão 0; sucessivos salvamentos com o mesmo nome geram versão 1, 2 e assim por diante. O método de salvamento retorna exatamente o número da versão atribuída. A recuperação padrão (`load_artifact` sem especificar versão) sempre traz a última versão disponível, mas é possível carregar versões específicas fornecendo o número da versão se necessário.

## Fluxo 1: Processamento de Áudio

**ETAPA 1.1 – Captura e preparação do áudio (Front-end):** Esta etapa ocorre no cliente (por exemplo, um aplicativo Flutter). O áudio da pergunta do usuário é gravado e convertido para bytes binários, pronto para envio ao backend. *Não há lógica do ADK aqui para validarmos; trata-se apenas da preparação dos dados pelo front-end.*

**ETAPA 1.2 – Backend recebe o áudio e cria um artifact:** No lado do servidor, quando a requisição do usuário contendo áudio chega, o sistema (seja o *runner* do ADK ou código custom do backend) precisa identificar os dados binários e armazená-los como um artifact antes de passar a informação ao agente. Conforme a documentação oficial, devemos criar um objeto `Part` a partir dos bytes recebidos e chamar o método de salvar artifact no contexto da sessão:

```python
audio_part = types.Part.from_bytes(audio_bytes, "audio/wav")
version = context.save_artifact(filename=filename, artifact=audio_part)
```

Isso armazenará os bytes do áudio no ArtifactService e retornará a versão atribuída. O nome de arquivo (`filename`) pode ser algo como `"pergunta_aluno_123.wav"`, incorporando talvez um timestamp para unicidade. De acordo com o ADK, após essa chamada, **o dado binário não trafega mais pelo prompt ou estado**, apenas a referência (nome e versão) fica registrada para uso posterior. *Na implementação do Professor Virtual, essa lógica de salvar o artifact do áudio deve ser realizada explicitamente.* Por exemplo, poderíamos imaginar que o Runner do ADK (ou um callback inicial) faça algo semelhante a acima assim que detecta um arquivo de áudio na query do usuário.

**ETAPA 1.3 – Armazenamento no GCS:** Uma vez salvo via `context.save_artifact`, se o ArtifactService configurado for persistente (GCS), o áudio é armazenado no bucket designado. O caminho de armazenamento seguirá o esquema:

```
gs://<bucket>/<app_name>/<user_id>/<session_id>/<filename>/<version>
```

No caso do **Professor Virtual**, o `app_name` configurado é `"professor_virtual_app"` (ver `Config.app_name` em `config.py`), portanto um exemplo de caminho seria: `professor_virtual_app/uid123/sess456/pergunta_aluno_123.wav/0` para a versão inicial. Isso está **alinhado com o comportamento documentado** – artefatos de escopo de sessão usam exatamente `app_name`, `user_id` e `session_id` no caminho. Já confirmamos que o ADK automaticamente lida com versionamento (criando a pasta/registro de versão *0* na primeira vez). O bucket específico (`adk-professor-virtual-artifacts`) provavelmente foi configurado ao iniciar o Runner com `GcsArtifactService`. *Como referência*, o ADK sugere usar `GcsArtifactService` para cenários onde desejamos persistência além do processo em memória.

**ETAPA 1.4 – Agente recebe apenas a referência:** Na interação com o modelo de IA, o agente **não recebe os bytes do áudio embutidos no prompt**. Em vez disso, o framework fornece ao agente uma referência textual ao artifact. Por exemplo, o prompt enviado ao agente pode conter algo como: *"Transcreva o áudio 'pergunta\_aluno\_123.wav'"*. Internamente, o ADK sabe que `"pergunta_aluno_123.wav"` corresponde a um artifact salvo e **não inclui o conteúdo binário na mensagem**, somente a chave/nome. A documentação deixa claro que os artifacts funcionam como ponteiros para dados binários grandes, evitando trafegar bytes dentro das mensagens. Assim, o agente (que é um LLM) pode decidir acionar a ferramenta de transcrição referenciando o nome do arquivo, enquanto o dado real permanece armazenado de forma separada.

**ETAPA 1.5 – Tool de transcrição acessa o artifact:** Quando o agente decide usar a ferramenta `transcrever_audio` para processar o áudio referenciado, essa função de ferramenta precisa carregar os bytes do artifact para trabalhar. A prática recomendada do ADK é utilizar o *ToolContext* fornecido para carregar o artifact pelo nome. Ou seja, a implementação deveria chamar:

```python
audio_artifact = tool_context.load_artifact(nome_artefato_audio)
```

Isto fará com que o ADK recupere os bytes do artifact (no nosso caso, do GCS via o ArtifactService) e retorne um objeto Part contendo os dados. De acordo com a documentação, ao chamar `load_artifact`, o ADK localiza automaticamente o artifact pelo `app_name`, `user_id` e `session_id` atuais, obtendo a versão mais recente salvo para aquele nome. O resultado será um `Part` com `inline_data` preenchido (data e mime type) se tudo ocorreu bem.

No código atual do **Professor Virtual**, notamos que as ferramentas estão usando um método ligeiramente diferente: elas chamam `tool_context.session.get_artifact(nome)` para obter o artifact diretamente da sessão. Por exemplo, na ferramenta de análise de imagem, vemos: `artifact = tool_context.session.get_artifact(nome_artefato_imagem)`. Essa abordagem funciona no contexto do projeto (e.g. retorna um objeto com os bytes em `artifact.content`, conforme a classe fake de teste), porém **a documentação oficial do ADK utiliza `load_artifact`** em vez de `get_artifact`. Ou seja, `load_artifact` é a API pública pensada para developers, enquanto `session.get_artifact` parece ser uma chamada interna ou legada. **Recomendação:** Alinhar o código à documentação, usando `tool_context.load_artifact(nome)` no lugar de acessar `session.get_artifact` diretamente. Isso garante compatibilidade futura e aproveita eventuais verificações extras do ADK (por exemplo, `load_artifact` retorna `None` se não encontrar o artifact, o que já é tratado no código com o `if not artifact:`). Em suma, para transcrição de áudio, a ferramenta deve carregar o artifact via contexto e então extrair os bytes (como já faz, lendo `artifact.content` ou `artifact.inline_data.data`). *A validação aqui é:* sim, o fluxo descrito está correto – o ADK provê `load_artifact` para recuperar os bytes do áudio e o código deve usá-lo conforme a documentação.

## Fluxo 2: Processamento de Imagem

**ETAPA 2.1 – Captura e preparação da imagem (Front-end):** Semelhante ao áudio, o cliente captura ou seleciona uma imagem (por exemplo, uma foto do exercício do aluno), e essa imagem é convertida para bytes e preparada para envio ao sistema. (Etapa puramente de front-end, não requer validação no código do agente.)

**ETAPA 2.2 – Backend cria artifact da imagem:** No backend, o processamento é análogo ao do áudio. Ao receber os bytes da imagem, cria-se um `Part` correspondente (por exemplo, `types.Part.from_bytes(image_bytes, "image/png")`) e salva-se no contexto da sessão com um nome de arquivo, por exemplo `"exercicio_ABC_123.png"`. A chamada seria `context.save_artifact(filename, image_part)` retornando a versão (0 na primeira vez). O resultado é que o artifact da imagem fica registrado no ArtifactService, associado à sessão atual. *No caso do projeto, espera-se que a imagem do exercício do aluno seja salva antes de chamar a ferramenta de análise.* Observando os testes unitários, vemos que antes de invocar `analisar_imagem_educacional` o código de teste injeta um artifact na sessão (FakeSession) com a key `"exercicio.png"`, simulando justamente que a imagem já foi salva no contexto. Ou seja, a arquitetura presume: **imagem recebida -> salva como artifact -> nome disponível para o agente/ferramenta.**

**ETAPA 2.3 – Storage com mesmo contexto de sessão:** A imagem é salva no mesmo escopo de sessão que o áudio anterior, o que é intencional para permitir correlação. Como discutido, usar um nome sem prefixo `"user:"` significa que tanto o áudio da pergunta quanto a imagem do exercício residem na sessão corrente do usuário. Isso garante que a ferramenta de análise de imagem possa acessar a imagem *e* ainda ter contexto da pergunta (áudio transcrito) dentro da mesma sessão. A documentação confirma que artifacts salvos na sessão atual ficam **disponíveis a todas as ferramentas e agentes daquela sessão**, compartilhando o mesmo “repositório” até que a sessão termine. *(Em cenários onde quiséssemos persistir a imagem para outras sessões futuras, usaríamos o prefixo de usuário, mas aqui o correto é mantê-la no escopo da conversa atual.)*

**ETAPA 2.4 – Tool de análise de imagem acessa o artifact:** Quando a ferramenta `analisar_imagem_educacional` é chamada pelo agente, ela precisa carregar os bytes da imagem salva. Novamente, o recomendado pelo ADK é usar `tool_context.load_artifact(nome_arquivo_imagem)`. No código **atual**, a implementação real dessa ferramenta (presente no repositório) segue a mesma convenção mencionada antes: utiliza `tool_context.session.get_artifact(nome)` para obter o artifact. Vemos isso no trecho de código real:

```python
artifact = tool_context.session.get_artifact(nome_artefato_imagem)
if not artifact:
    return { "erro": f"Artefato ... não encontrado", "sucesso": False, ...}
imagem_bytes = artifact.content  # obtém os bytes da imagem
```

Esse trecho deixa claro que *artifact* aqui possui um atributo `.content` com os bytes da imagem (no caso do FakeArtifact dos testes, `.content` carrega os bytes em memória). Novamente, **validamos que a sugestão dada procede**: a documentação oficial mostra o uso de `load_artifact` em vez de `get_artifact` diretamente. Portanto, a ferramenta deveria preferencialmente ser implementada como:

```python
image_part = tool_context.load_artifact(nome_artefato_imagem)
if not image_part:
    return { "erro": "Artifact não encontrado", ... }
imagem_bytes = image_part.inline_data.data
```

Isso manteria a consistência com a API do ADK. De resto, todo o fluxo da ferramenta (validação de tamanho, chamada ao modelo Gemini Vision, parsing da resposta) não envolve o sistema de artifacts em si, então está fora do escopo desta validação. O importante é que *cada detalhe relativo aos artifacts condiz com o esperado:* a ferramenta carrega o artifact pelo nome e obtém os bytes para análise. A única diferença é a troca de `session.get_artifact` (utilizada no código legado do projeto) pelo `context.load_artifact` (conforme documentação) – uma mudança recomendada para aderência às melhores práticas do ADK.

## Fluxo 3: Geração de Áudio TTS

**ETAPA 3.1 – Tool gera áudio de resposta e salva artifact:** Aqui o agente (Professor Virtual) vai gerar uma resposta em áudio para o usuário, utilizando a ferramenta `gerar_audio_tts`. Conforme analisado, a implementação atual **gera** os bytes de áudio (convertendo do formato PCM base64 retornado pelo modelo Gemini TTS para um WAV, e eventualmente mantendo extensão `.mp3` por compatibilidade) e então **salva o resultado como um artifact** na sessão. No código, isso é feito com a chamada:

```python
nome_artefato = f"resposta_tts_{uuid.uuid4()}.mp3"
tool_context.session.create_artifact(
    name=nome_artefato,
    content=audio_bytes,
    mime_type="audio/mpeg"
)
```

. Essa linha insere o artifact do áudio de resposta no armazenamento da sessão – nos testes, por exemplo, após chamar `gerar_audio_tts`, verificamos que `result["nome_artefato_gerado"]` realmente consta em `session.artifacts` (ou seja, foi salvo).

Vamos validar os detalhes dessa implementação com a documentação:

* **Uso de `create_artifact`:** A documentação do ADK para Python não menciona um método `create_artifact` no contexto, e sim o método `save_artifact` no *CallbackContext/ToolContext*. De fato, o exemplo oficial sugere criar um objeto Part e utilizar `context.save_artifact(nome, artifact_part)`. Portanto, a sugestão de usar a “nova API” é correta. Em vez de passar os bytes diretamente para `session.create_artifact`, o ideal seria:

  ```python
  audio_part = types.Part.from_bytes(audio_bytes, "audio/mpeg")
  version = tool_context.save_artifact(nome_artefato, audio_part)
  ```

  Isso aproveita o mecanismo do ADK de versionamento e armazenamento de forma mais explícita. No entanto, é importante notar que, funcionalmente, o que o código atual faz é salvar na sessão (via método do FakeSession ou do ArtifactService interno) o artifact. A análise de compatibilidade realizada no projeto indicou que esse uso estava correto e seguindo o padrão esperado (provavelmente porque o ADK 1.5 ainda oferece `session.create_artifact` como caminho, ou simplesmente porque o FakeSession implementou dessa forma). *Mas a documentação oficial* reforça o uso de `save_artifact` no contexto do callback ou ferramenta, o que confirma a recomendação de ajuste. Em suma, **sim, a implementação complementar sugerida está correta**: devemos criar um `Part` do áudio e usar `tool_context.save_artifact` conforme o ADK espera. Isso garantirá que obtenhamos o número de versão de retorno e sigamos a interface pública documentada (evitando chamadas diretas a métodos de sessão não documentados).

* **Nome do artifact gerado:** O formato sugerido `"resposta_tts_<UUID>.mp3"` é adequado. Conforme discutido, a extensão em si não afeta a lógica, mas é boa prática incluí-la. O mime type usado `"audio/mpeg"` corresponde ao `.mp3` pretendido, o que está correto e importante para que o ADK/serviços saibam do que se trata.

* **Estado da sessão (metadados):** O complemento menciona que se poderia usar a API antiga e que foi usada. De fato, o código adiciona alguns metadados em `tool_context.state` (como `ultimo_audio_tts`) após criar o artifact. Isso é um detalhe extra de implementação do projeto (guardar no estado da sessão informações sobre o áudio gerado) e não impacta o sistema de artifacts em si – portanto não necessitamos validar com a documentação ADK, além de notar que é possível graças ao fato do *ToolContext* permitir escrita no estado.

**ETAPA 3.2 – Artifact disponível para download:** Após a ferramenta gerar o áudio e salvá-lo, o agente provavelmente retorna ao usuário alguma referência a esse artifact – possivelmente o próprio nome de arquivo gerado (`nome_artefato_gerado`) – para que o cliente possa obter o áudio. Existem algumas maneiras de entregar o áudio ao usuário final:

1. **Via link GCS assinado:** Sabendo o bucket e o caminho (e tendo permissões), o front-end poderia baixar o arquivo diretamente do armazenamento. Por exemplo, criar uma URL assinada para `.../resposta_tts_xyz.mp3/0`.
2. **Via API do Runner:** O cliente poderia fazer uma requisição para o backend (Runner ADK) pedindo o conteúdo do artifact pelo nome, e o backend usaria `load_artifact` e retornaria os bytes.
3. **Streaming inline (se pequeno):** Não é o caso aqui, pois decidimos usar artifacts justamente para não enviar bytes grandes diretamente.

O importante é: **a documentação do ADK suporta esse fluxo de download de artifacts pelo usuário.** Um dos casos de uso descritos oficialmente é possibilitar que arquivos gerados pelo agente sejam posteriormente recuperados ou baixados pelo usuário. Portanto, a etapa final descrita – de o frontend receber o nome do arquivo de áudio e então baixar o conteúdo – está alinhada com as intenções do ADK. No contexto do **Professor Virtual**, muito provavelmente o agente devolve na resposta algo como *"Arquivo de áudio gerado: resposta\_tts\_12345.mp3"* e então o app cliente sabe que deve buscar esse arquivo para reproduzir o áudio de resposta para o aluno. Novamente, verificamos que tudo isso é possível graças ao artifact ter sido salvo (persistido) e identificado por nome e versão.

## Gestão de Sessão e Persistência de Artifacts

Reforçando os pontos validados sobre escopo e persistência:

* **Artifacts de Sessão:** Por padrão, quaisquer artifacts salvos sem prefixo ficam restritos à sessão corrente. No nosso exemplo, `"pergunta_aluno_123.wav"`, `"exercicio_abc.png"` e `"resposta_tts_xyz.mp3"` são específicos de uma sessão de conversa. O ADK armazena esses arquivos sob a chave desse `session_id`, e ao encerrar a sessão eles deixam de ser acessíveis em sessões futuras (a não ser que sejam explicitamente repassados). Essa separação garante isolamento entre conversas diferentes. Os caminhos no storage incluem o ID da sessão como vimos, e a documentação destaca que artifacts assim **só são acessíveis naquela sessão** – confirmando a descrição do complemento.

* **Artifacts de Usuário:** Quando precisamos que um artifact perdure entre sessões (por exemplo, um histórico de dúvidas do aluno, preferências de voz, ou um avatar de perfil), utilizamos o prefixo `"user:"`. Os exemplos dados (`"user:historico_duvidas.json"`, `"user:preferencias_audio.json"`, `"user:avatar.png"`) indicam exatamente isso: arquivos associados ao usuário e não a uma única sessão. O ADK trata esses nomes com prefixo especial mapeando-os para um escopo de usuário. Internamente, em vez de usar o `session_id` no caminho, ele utiliza um identificador fixo (literalmente `'user'` ou equivalente) para armazená-los, tornando-os acessíveis de qualquer sessão desse usuário. A documentação oficial confirma essa funcionalidade e adverte para usar esse recurso apenas quando realmente faz sentido compartilhar dados entre sessões do mesmo usuário. A representação de path mencionada no complemento (`.../user/filename/version`) condiz com essa lógica – na prática o ArtifactService reconhece `"user:"` e direciona para um namespace separado de sessão.

* **Versionamento Automático:** A descrição de versionamento no complemento está correta e é comprovada pelas docs. Na primeira vez que chamamos `save_artifact("exercicio.png", image_part)` obteremos a versão 0. Se, por exemplo, a ferramenta de gerar áudio TTS salvasse um arquivo com o mesmo nome em outro momento (mesmo usuário e sessão), a versão retornada seria 1, e assim por diante. O ADK gerencia isso automaticamente e permite inclusive listar versões ou carregar versões antigas se necessário. No caso do Professor Virtual, não vimos no código nenhuma lógica manual de versão, o que é bom – confiamos no mecanismo embutido. O relatório complementar cita `version = context.save_artifact(...)` armazenando `version_0`, o que reflete exatamente o comportamento esperado.

**Conclusão desta validação:** Cada detalhe sugerido no complemento foi verificado em relação ao código do projeto e à documentação oficial do Google ADK. Os conceitos de artifacts, seu armazenamento, escopos e uso pelas ferramentas estão em conformidade com o que o ADK define. Onde a implementação do projeto diverge levemente da documentação (uso de `session.get_artifact`/`create_artifact` vs `load_artifact`/`save_artifact`), confirmamos através das fontes oficiais que a sugestão de mudança é procedente. Em suma, o **sistema de artifacts do Professor Virtual** está corretamente arquitetado e as melhorias apontadas visam apenas alinhá-lo ainda mais às práticas recomendadas pelo ADK, assegurando consistência e manutenção futura. Cada fluxo – do upload do áudio/imagem até a geração e disponibilização de resposta em áudio – segue o desenho esperado pelo framework, conforme validado ponto a ponto com a documentação e com trechos do próprio código fonte do projeto. Assim, podemos afirmar com segurança que as informações complementares estão **validadas e corretas** dentro do contexto do Google ADK e da implementação do Professor Virtual.

**Referências Utilizadas:**

* Documentação oficial do Google ADK (Agent Development Kit) – seções sobre **Artifacts**, **Context/ToolContext** e **gerenciamento de arquivos**, entre outras.
* Código do repositório `drdanielnutro/customer-service` (Projeto **Professor Virtual**) – arquivos de ferramentas e configuração, incluindo `analisar_imagem_educacional.py` e `gerar_audio_tts.py`, além dos testes unitários relacionados, para confirmar o comportamento atual e simulado do sistema de artifacts.
