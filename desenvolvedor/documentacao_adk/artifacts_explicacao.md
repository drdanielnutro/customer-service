# Uso de Artifacts do Google ADK para Dados de Imagem e Áudio

## Visão Geral dos **Artifacts** no ADK

No **Google Agent Development Kit (ADK)**, *Artifacts* são um mecanismo criado para gerenciar dados binários (imagens, áudio, PDF, etc.) de forma eficiente dentro de agentes e ferramentas. Um **Artifact** representa um pedaço de dados binários identificado por um nome único (*filename*) e é versionado automaticamente a cada vez que é salvo. Esses artefatos podem ser vinculados a uma **sessão específica** ou a um **usuário** (escopo mais amplo), dependendo de como nomeamos o arquivo (por exemplo, prefixando com `"user:"` para torná-lo compartilhado em todas as sessões do usuário). A principal função dos Artifacts é permitir que agentes e ferramentas manipulem dados além de simples texto, incluindo **arquivos, imagens, áudio e outros formatos binários**. Em resumo, os Artifacts fornecem aos agentes um meio **nativo** de lidar com conteúdo binário de forma estruturada e integrada à sessão, sem precisar trafegar esses bytes diretamente nas mensagens de texto da conversa.

## Por que usar Artifacts para Imagens e Áudio?

Usar Artifacts no ADK traz **várias vantagens** para manipular imagens, áudio ou outros binários, ao invés de inseri-los diretamente em strings (por exemplo, via Base64):

* **Manuseio de Dados Não-textuais:** Os Artifacts permitem **armazenar e recuperar facilmente imagens e clipes de áudio**, além de vídeos, PDFs, planilhas ou qualquer outro formato necessário para a função do agente. Isso significa que um agente pode, por exemplo, salvar uma imagem gerada ou recebida e posteriormente outra ferramenta ou sub-agente pode acessá-la pelo nome, sem precisar reencodificar em texto.
* **Persistência de Dados Grandes:** Diferente do `session.state` (estado da sessão) que é ideal para pequenos trechos de informação (strings, números, etc.), os Artifacts foram projetados para **dados binários volumosos**. Eles fornecem um mecanismo dedicado para persistir blobs grandes sem sobrecarregar ou “poluir” o estado da sessão. Isso evita, por exemplo, ter que passar strings Base64 enormes entre ferramentas, já que o conteúdo bruto fica guardado separadamente.
* **Compartilhamento e Reutilização de Resultados:** Uma vez salvo, um Artifact pode ser **compartilhado entre diferentes componentes do agente**. Ferramentas ou agentes podem gerar saídas binárias (uma imagem gerada por IA, um relatório PDF, um áudio sintetizado) e salvá-las via `save_artifact`. Mais tarde, **outras partes da aplicação ou mesmo sessões subsequentes** podem carregar esses dados pelo nome do artifact. Em outras palavras, o artifact funciona como um **repositório comum** onde ferramentas e agentes depositam e buscam dados, em vez de repassar a informação crua diretamente de um para outro.
* **Evitar Re-Processamento e Redundância:** Como os artefatos são versionados e podem ser consultados sob demanda, o agente pode **cachear resultados binários** custosos de produzir. Por exemplo, se uma ferramenta gerou uma imagem complexa ou realizou uma conversão de áudio, o resultado pode ser armazenado como artifact; assim, requisições futuras podem simplesmente carregar esse artifact ao invés de recomputar tudo. Isso é mais eficiente do que recalcular ou retransmitir dados pesados repetidamente.

Em essência, **sempre que o agente precisar lidar com dados “tipo arquivo”** que precisem ser **persistidos, versionados ou compartilhados**, os Artifacts são o mecanismo apropriado no ADK. Essa abordagem elimina a necessidade de intercambiar grandes blobs binários dentro de prompts ou estados em texto (como strings Base64), pois o ADK gerencia esses dados de forma própria.

## Como os Artifacts Mantêm Dados na Sessão (Referência vs. Cópia)

O ponto chave do ADK é que os Artifacts **não são passados diretamente** entre ferramentas em formato bruto; em vez disso, eles ficam armazenados por um serviço dedicado (**ArtifactService**) e são referenciados por nome dentro da sessão atual. Vamos detalhar este funcionamento:

* **Armazenamento Centralizado via ArtifactService:** Quando você configura seu agente com um *ArtifactService* (por exemplo, `InMemoryArtifactService` para armazenar em memória, ou `GcsArtifactService` para usar o Google Cloud Storage), esse serviço age como um **repositório central** para todos os artifacts daquela execução. O serviço é fornecido ao inicializar o *Runner* do ADK e, a partir daí, **fica disponível a todos os componentes** (agentes, ferramentas, callbacks) por meio do contexto de invocação. Assim, qualquer parte do agente que tenha acesso ao contexto da sessão pode chamar métodos como `save_artifact` ou `load_artifact`.
* **Salvando um Artifact (referência criada):** Suponha que uma ferramenta de código Python gere uma imagem a partir de um prompt do usuário. Em vez de devolver os bytes da imagem codificados, a ferramenta pode fazer: `context.save_artifact("resultado.png", artifact_part)`. Isso salva os bytes no *ArtifactService* sob o nome `"resultado.png"` e retorna um número de versão. Importante: **o dado binário em si não transita mais na mensagem**; apenas um registro do artifact (nome e versão) fica registrado no evento da sessão. Conforme a documentação, após salvar, o evento associado conterá a informação `artifact_delta` indicando qual artifact e versão foram adicionados.
* **Carregando/Usando um Artifact (via referência):** Posteriormente, se outro *tool* ou mesmo o agente precisar daquele dado (por exemplo, para enviar a imagem de volta ao usuário ou fazer mais processamento), ele utiliza o **nome do artifact** para recuperá-lo: `data = context.load_artifact("resultado.png")`. O ADK então busca os bytes armazenados para `"resultado.png"` no ArtifactService e os retorna (por padrão, pega a versão mais recente). Novamente, isso ocorre **dentro do backend** – o agente não precisava receber a imagem via texto antes, ele apenas solicitou pelo nome. Ou seja, **o artifact funciona como referência persistente aos dados dentro da sessão**. Essa referência (nome do arquivo) **está sempre disponível** no contexto da sessão para qualquer componente que precise acessar aquele conteúdo. Ferramentas e callbacks veem o mesmo "espaço de artifacts" atrelado à sessão.
* **Disponibilidade para Ferramentas, Subagentes e Functions:** Dado que o *ArtifactService* é configurado no nível do Runner (que executa o agente) e ligado ao contexto da invocação, todas as ferramentas e mesmo *subagentes* executados dentro daquela sessão **podem compartilhar artifacts**. No caso de um *AgentTool* (um agente usado como ferramenta de outro), o ADK inclusive se encarrega de **propagar as alterações de artifacts de volta para o contexto do agente pai**. Isso significa que se um subagente salvar um artifact durante sua execução, ao terminar, esse artifact aparece no contexto do agente chamador (pai). Da mesma forma, se já existirem artifacts no contexto do pai, o subagente pode acessá-los *desde que saiba os nomes* – contudo, vale notar que há discussões na comunidade sobre passar automaticamente referências de artifacts para subagentes; a prática recomendada é colocar, por exemplo, o nome do artifact no estado ou na mensagem para o subagente, ou usar um prefixo `"user:"` se for um artifact de escopo global do usuário. Em síntese, **dentro de uma mesma sessão, todos os componentes compartilham o mesmo repositório de artifacts**, bastando usar o nome correto para acessar cada item.

**Importante:** Os artifacts **não ficam armazenados no estado da sessão** diretamente, nem nas mensagens trocadas. Eles residem no *ArtifactService* configurado (em memória ou armazenamento externo), e o que a sessão guarda é apenas a *chave* (nome e versão) para recuperá-los quando necessário. Esse design evita duplicação de dados e mantém as mensagens leves, pois você não precisa inserir um string Base64 enorme ou bytes brutos no meio da conversa. Em vez disso, você tem algo como um ponteiro para os dados binários, que o ADK sabe resolver quando for preciso carregar ou enviar esses dados.

## Escopo de **Sessão** vs. Persistência de Usuário

Pelo comportamento padrão, um artifact salvo é **específico daquela sessão** de interação do usuário com o agente. Ou seja, se você salva um artifact com um nome simples (por exemplo `"foto.png"`) ele fica vinculado internamente à combinação de `app_name + user_id + session_id` atuais. Isso quer dizer que **somente naquela sessão** esse artifact estará acessível. Se o usuário iniciar uma nova sessão (novo chat, por exemplo), por padrão não terá acesso aos artifacts da sessão anterior a menos que:

* **Uso de Namespacing de Usuário:** O ADK suporta salvar artifacts com escopo de usuário. Para isso, prefixamos o nome do artifact com `"user:"` – por exemplo, `"user:foto.png"`. Ao fazer isso, o artifact é armazenado associado apenas ao `app_name` e `user_id`, **sem amarrar a um session\_id específico**. Dessa forma, qualquer sessão futura do mesmo usuário (dentro do mesmo app) pode carregar `"user:foto.png"`. Esse recurso é útil para dados que precisam persistir entre sessões, mas deve ser usado conscientemente (pode haver implicações de privacidade e armazenamento prolongado).
* **Serviços de Artifact Persistentes:** Se o objetivo for guardar dados binários de forma duradoura (por exemplo, imagens geradas que o usuário possa recuperar dias depois), é recomendável usar um `ArtifactService` persistente, como o `GcsArtifactService` (Google Cloud Storage). Com isso, mesmo que o processo reinicie ou expire, os artifacts persistem externamente. Já o `InMemoryArtifactService` (geralmente usado em desenvolvimento ou testes) guarda os dados **apenas na memória do processo**, ou seja, dura somente enquanto a aplicação estiver rodando e, tipicamente, isolado por sessão.

No contexto da pergunta, o entendimento do usuário estava focado em *“apenas na sessão”*. Sim, por padrão **os artifacts são atrelados à sessão corrente** – qualquer ferramenta, subagente ou function tool dentro dessa sessão pode utilizá-los livremente, mas fora dali eles não existem a menos que se opte pelo escopo de usuário ou outro mecanismo de persistência. Portanto, **o entendimento está correto:** na utilização típica, os artifacts servem para manter os dados binários **dentro da sessão**, evitando a passagem direta de bytes entre ferramentas e garantindo que todos os componentes possam acessar esses dados via referência.

## Exemplo Resumido de Uso (Python ADK)

Para ilustrar, considere um cenário prático em Python:

1. **Configuração do ArtifactService:** Ao iniciar o agente, passamos uma instância de ArtifactService para o Runner. Exemplo: `runner = Runner(agent=my_agent, app_name="my_app", session_service=InMemorySessionService(), artifact_service=InMemoryArtifactService())`. Isso habilita o uso de artifacts no contexto. Se não fizéssemos isso, chamadas a `context.save_artifact` resultariam em erro, pois nenhum serviço de artifact estaria disponível.

2. **Salvando uma imagem como Artifact:** Suponha que uma ferramenta gerou bytes de imagem (`image_bytes`) após alguma operação. Podemos criar um objeto `Part` (que encapsula os bytes e o MIME type, e é a representação padrão de artifact no ADK) e então salvar:

   ```python
   image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
   version = await context.save_artifact(filename="resultado.png", artifact=image_part)
   print(f"Artifact salvo como versão {version}.")
   ```

   Isso irá armazenar `image_bytes` dentro do ArtifactService associado à sessão, sob o nome `"resultado.png"`. Nenhum dado da imagem precisou ser colocado no estado ou retornado em texto – apenas a referência `"resultado.png"` (e a versão) foi registrada.

3. **Usando o Artifact em outra ferramenta ou resposta:** Mais tarde, se quisermos usar essa imagem, simplesmente carregamos:

   ```python
   artifact_part = await context.load_artifact("resultado.png") 
   image_data = artifact_part.inline_data.data  # bytes da imagem
   mime = artifact_part.inline_data.mime_type   # por exemplo, "image/png"
   ```

   Assim obtemos os mesmos bytes de volta. Podemos então, por exemplo, retornar isso para o usuário (se o front-end suportar mostrar imagens), ou processá-los em outra função. O ponto crucial é que **qualquer parte do código dentro da sessão pode chamar `load_artifact("resultado.png")` e obter os dados**, contanto que conheça o nome do artifact.

4. **Limpeza e versões:** Caso salve novamente outro conteúdo com o mesmo nome `"resultado.png"`, o ArtifactService criará uma **nova versão**. Podemos listar versões e até deletar artifacts via métodos apropriados (esses detalhes fogem do escopo aqui, mas o ADK dá controle sobre versões e limpeza se necessário). Para muitos casos de uso, porém, basta usar sempre o nome fixo se quiser substituir o conteúdo antigo, ou nomes diferentes para artifacts diferentes.

## Conclusão

O **entendimento do usuário está correto**: o Google ADK introduz um sistema de artifacts justamente para **evitar a passagem manual de dados binários** (como strings Base64) entre ferramentas ou agentes. Em vez disso, os dados de imagens, áudios e outros arquivos ficam armazenados no contexto da sessão via um serviço dedicado, e **os componentes do agente trocam apenas referências (nomes/identificadores) a esses artifacts**. Dessa forma, qualquer ferramenta, subagente ou função dentro da sessão pode acessar o dado quando precisar, usando a referência adequada, sem precisar retransmitir ou reprocessar o conteúdo original a cada passo.

Em suma, o ADK **mantém os dados binários vinculados à sessão**, permitindo interações ricas (upload/download de arquivos, geração de imagens, síntese de áudio, etc.) com facilidade e eficiência. Essa abordagem confirma que, ao usar artifacts, o desenvolvedor obtém uma camada de gerenciamento de arquivos integrado ao ciclo de conversação do agente, o que simplifica bastante o design de agentes multimodais. Portanto, *sim, sua compreensão está correta* – e conforme vimos, o foco está em aproveitar o ArtifactService do ADK para referenciar os dados dentro da sessão, garantindo disponibilidade para quem precisar usá-los, sem espalhar bytes brutos pelas mensagens.

**Referências Utilizadas:**

* Documentação oficial do Google ADK sobre Artifacts
* Guia *About ADK* com resumo das capacidades de Artifact Management
* Comentário de revisor (Reddit) destacando a utilidade dos artifacts para armazenar/carregar binários atrelados à sessão
* Documentação de sistemas multi-agentes do ADK, explicando propagação de artifacts para subagentes (AgentTool)
* Trechos da seção “Why Use Artifacts?” da documentação oficial, exemplificando casos de uso com imagens e áudio
