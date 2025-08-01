# Dúvida:
3. Tratamento de Erros

  Minha interpretação: A documentação menciona que chamar métodos de artifact quando o artifact_service é None resulta em ValueError.

  Pergunta: É necessário capturar especificamente ValueError além de Exception genérica? Existem outros erros específicos documentados?

# Resposta:
1. Princípios e Melhores Práticas de Tratamento de Erros no ADK
A documentação do Google ADK não apresenta uma seção centralizada dedicada às melhores práticas de tratamento de erros. No entanto, a análise de guias de desenvolvimento e princípios de engenharia de software revela uma forte preferência pelo uso de exceções em vez de códigos de retorno para gerenciar erros. As práticas recomendadas, alinhadas com o desenvolvimento robusto em Python, incluem:

Falha Rápida e Imediata: Erros devem ser levantados no momento em que são detectados para prevenir estados inconsistentes e simplificar a depuração.
Especificidade na Captura: É fundamental capturar a exceção mais específica possível. Esta prática torna o código mais claro, seguro e evita o tratamento acidental de erros inesperados que deveriam propagar e potencialmente encerrar o programa.
Uso Cauteloso da Captura Genérica: Blocos except Exception: devem ser utilizados estrategicamente, principalmente como uma última barreira para registrar erros imprevistos (logging) e evitar que a aplicação trave, em vez de serem usados para a lógica de controle principal.
Validação em Ferramentas (Tools): Ao desenvolver ferramentas personalizadas, recomenda-se levantar um ValueError para sinalizar que os dados de entrada, embora do tipo correto, são inválidos para a operação.
Gerenciamento de Recursos: Ao interagir com recursos externos, como arquivos ou conexões de rede, o uso do bloco finally garante que esses recursos sejam sempre liberados, independentemente da ocorrência de uma exceção.
2. Exceções Específicas vs. Genéricas: Análise Comparativa
A documentação do ADK não fornece orientação explícita sobre a captura de exceções, mas as melhores práticas em Python oferecem uma diretriz clara: capturar a exceção mais específica possível. A captura genérica de Exception deve ser reservada para os níveis mais altos de um programa, principalmente para fins de log e para impedir que a aplicação encerre inesperadamente.

A tabela a seguir detalha a comparação entre as duas abordagens no contexto do desenvolvimento com o ADK.

Característica	Captura de Exceção Específica (ex: except ValueError:)	Captura de Exceção Genérica (ex: except Exception:)
Cenário de Uso Principal	Tratar uma condição de erro conhecida e esperada para a qual uma lógica de recuperação pode ser implementada.	Atuar como uma "rede de segurança" para capturar erros inesperados e desconhecidos.
Exemplo no ADK	Capturar o ValueError que ocorre ao chamar context.save_artifact() sem um ArtifactService configurado no Runner.	Envolver uma chamada de ferramenta que interage com uma API externa, onde podem ocorrer diversas falhas (rede, autenticação, etc.).
Clareza do Código	Alta. A intenção do código é explícita; ele foi projetado para lidar com aquele erro específico.	Baixa. Pode mascarar a intenção, pois o bloco tenta lidar com qualquer tipo de falha.
Segurança e Robustez	Alta. Evita a captura acidental de outros erros (como TypeError ou MemoryError), permitindo que eles se propaguem e revelem bugs.	Média/Baixa. Risco de "engolir" exceções críticas que deveriam parar a execução, deixando a aplicação em um estado inconsistente.
Lógica de Recuperação	Permite uma lógica de recuperação direcionada. Por exemplo, notificar o usuário para configurar o serviço ou solicitar uma entrada válida.	Geralmente, permite apenas uma recuperação genérica, como exibir uma mensagem de "erro inesperado" e registrar o traceback para depuração.
Quando Escolher	Quando a documentação (ou a implementação de uma ferramenta) indica claramente que uma exceção específica pode ser levantada e você pode fazer algo a respeito.	No nível mais alto de um fluxo de execução (por exemplo, no loop principal de um servidor) para garantir que a aplicação não trave, focando em logar o erro.
3. A Exceção ValueError: Contextos e Casos de Uso
A análise da documentação da API do ADK e de materiais de suporte revela vários contextos onde a exceção ValueError é levantada.

Chamada de Métodos de Artefato sem ArtifactService: O caso mais proeminente ocorre se os métodos save_artifact, load_artifact ou list_artifacts forem invocados sem que um ArtifactService tenha sido fornecido ao Runner durante a inicialização. Isso ocorre porque o ADK não possui a lógica necessária para persistir ou recuperar os dados do artefato. github.io
Validação de Entradas em Ferramentas: Em tutoriais e exemplos de código, ValueError é levantado dentro de ferramentas customizadas para indicar que os argumentos fornecidos são inválidos para a lógica da ferramenta. Por exemplo, validar um formato de data/hora ou garantir que uma lista de itens não está malformada. google.com
Configuração de Ambiente: Em um tutorial, um ValueError é levantado se variáveis de ambiente necessárias (como chaves de API) não forem definidas antes de inicializar os serviços. wandb.ai
Problemas Internos em Serviços Dependentes: O GcsArtifactService pode levantar um ValueError internamente se a estrutura de nomes de blobs no Google Cloud Storage não corresponder ao formato esperado. Isso pode acontecer ao usar o Vertex AI session service em conjunto com o GCS artifact service, devido a uma expectativa de formatação de nome de blob que não é atendida. github.com
4. Catálogo de Exceções Documentadas no ADK
A pesquisa indica que o ADK se baseia primariamente nas exceções built-in do Python em vez de definir um conjunto extenso de exceções customizadas. A principal exceção documentada que os desenvolvedores devem tratar proativamente é a ValueError.

A tabela a seguir cataloga as condições de erro documentadas ou inferidas a partir de exemplos.

Exceção	Condição em que Ocorre	Contexto no ADK	Ação Recomendada
ValueError	Tentativa de uso de save_artifact, load_artifact ou list_artifacts quando o artifact_service no Runner é None.	Interação com o adk.ArtifactService através do objeto de contexto.	Capturar ValueError especificamente. Notificar o usuário ou registrar um erro de configuração. Garantir que um ArtifactService seja fornecido ao Runner.
ValueError	Argumentos passados para uma ferramenta são do tipo correto, mas semanticamente inválidos (ex: formato de data incorreto, valor fora de um intervalo esperado).	Dentro da implementação de uma ferramenta (Tool) customizada.	Levantar ValueError na sua ferramenta para sinalizar o problema. O código que chama a ferramenta deve capturá-lo para fornecer feedback ao usuário.
ValueError	O GcsArtifactService encontra um nome de blob no GCS que não corresponde à estrutura de diretório esperada. github.com	Ocorre internamente no GcsArtifactService, especialmente quando usado com o Vertex AI session service.	Capturar Exception para logar o erro. Este é um erro de nível mais baixo que indica um problema de integração ou um bug.
Exception (genérica)	Erros de I/O, rede, permissões ou outras falhas inesperadas ao interagir com serviços externos (ex: Google Cloud Storage).	Dentro de ferramentas que dependem de recursos externos, ou durante a operação do GcsArtifactService.	Capturar Exception para registrar o erro detalhadamente (logging) e fornecer uma resposta de falha genérica, evitando que a aplicação trave.