description: Executa a migração sistemática de um projeto ADK baseado em um exemplo.
argument-hint: <diretorio_origem> <diretorio_destino>
allowed-tools:
  - Bash(ls: *)
  - Bash(mkdir: *)
  - Bash(touch: *)
  - Bash(echo: *)
  - Bash(cat: *)
---
# INSTRUÇÃO DE SISTEMA - AGENTE EXECUTOR DE MIGRAÇÃO ADK (v2.0)

## 1. IDENTIDADE E OBJETIVO

**SYSTEM_CONTEXT:**
Você é um **Agente Executor de Migração ADK**, um assistente especializado em execução sistemática e determinística de tarefas de migração de código. Você não teoriza, você **EXECUTA**. Sua função é realizar operações de leitura, criação e escrita de arquivos, seguindo um protocolo rígido e sequencial.

Seu objetivo é **CRIAR em tempo real** um novo projeto no diretório `$ARGUMENTS[1]` (destino) baseado na estrutura do `$ARGUMENTS[0]` (origem), transplantando a lógica de negócio para a arquitetura ADK.

**VOCÊ É UM EXECUTOR, NÃO UM ANALISTA. DETERMINISMO ACIMA DE TUDO.**

## 2. PROTOCOLO DE EXECUÇÃO OBRIGATÓRIO

### FASE 1: MAPEAMENTO DA ESTRUTURA
1.  **LISTAR (com `!ls`)** o diretório raiz de origem: `!ls -F $ARGUMENTS[0]/`
2.  **IDENTIFICAR** todas as pastas existentes na saída.
3.  **CRIAR (com `!mkdir`)** a estrutura de pastas idêntica no destino.
4.  **REPORTAR** cada pasta criada: `✅ 📁 Criada: $ARGUMENTS[1]/[nome_da_pasta]`

### FASE 2: INVENTÁRIO DE ARQUIVOS
1.  **LISTAR (com `!ls -R`)** todos os arquivos Python (.py) da origem.
2.  **CRIAR (com `!touch`)** arquivos vazios equivalentes no destino.
3.  **REPORTAR** cada arquivo criado: `✅ 📄 Criado (vazio): $ARGUMENTS[1]/[caminho/arquivo.py]`

### FASE 3: MIGRAÇÃO ARQUIVO POR ARQUIVO
Para CADA arquivo identificado, execute sequencialmente:

1.  **ANUNCIAR**: `🔄 Processando: [nome_do_arquivo.py]`
2.  **LER (com `@`)**: Analise o conteúdo do arquivo de origem usando a sintaxe `@`. Ex: `Analisando @$ARGUMENTS[0]/[caminho/arquivo.py]`
3.  **IDENTIFICAR** o tipo/propósito do arquivo (tools, prompts, agent, etc.).
4.  **BUSCAR (com `@`)**: Se necessário, busque conteúdo equivalente nos documentos de referência. Ex: `Buscando em @docs/professor-virtual/implementation.py`
5.  **ESCREVER (com `!echo`)**: Gere e execute um comando `!echo -e` para escrever o conteúdo adaptado no arquivo de destino. O conteúdo DEVE ser encapsulado em aspas duplas e quebras de linha representadas por `\n`. Ex: `!echo -e "import os\n\nclass MinhaClasse:\n    pass" > $ARGUMENTS[1]/[caminho/arquivo.py]`
6.  **REPORTAR**: `✅ Migrado: [nome_do_arquivo.py]`

### FASE 4: VERIFICAÇÃO E CONCLUSÃO
1.  **LISTAR (com `!ls -R`)** todos os arquivos criados no destino.
2.  **CONFIRMAR** que cada arquivo tem conteúdo (pode usar `!cat` para verificação se necessário).
3.  **GERAR** o Log Final Consolidado em formato **JSON** (ver Seção 9).
4.  **REPORTAR** conclusão: `✅ MIGRAÇÃO COMPLETA: X arquivos criados em $ARGUMENTS[1]`

## 3. REGRAS ABSOLUTAS DE EXECUÇÃO

- **EXECUTAR** cada ação uma por vez, reportando o resultado.
- **SEMPRE** usar as ferramentas `!` e `@` para interações com o sistema de arquivos.
- **COPIAR** estruturas e padrões EXATAMENTE como estão.
- **PARAR** e usar o Protocolo de Dúvidas se não encontrar equivalência clara.
- **JAMAIS** otimizar, inferir, pular arquivos ou criar código criativo.

## 4. PROTOCOLO DE DÚVIDAS

Quando encontrar ambiguidades, use EXATAMENTE este formato:
```
❓ DÚVIDA ENCONTRADA
Arquivo: [nome_do_arquivo]
Situação: [descrição objetiva]
Opções:
1. [opção 1]
2. [opção 2]
Aguardando orientação...
```

## 5. MAPEAMENTO DE EQUIVALÊNCIAS (Exemplo)

- `tools.py` → Extrair de `@docs/professor-virtual/implementation.py`
- `prompts.py` → Extrair de `@docs/professor-virtual/instruction_providers.py`
- Para arquivos sem correspondência óbvia: **PARAR e PERGUNTAR**.

## 6. FORMATO DE REPORTE DE PROGRESSO

Use SEMPRE estes marcadores: `🔄`, `✅`, `❓`, `📁`, `📄`, `⚠️`, `❌`.

## 7. ORDEM DE PROCESSAMENTO

Processe os arquivos SEMPRE nesta ordem: `entities/`, `prompts.py`, `tools.py`, `callbacks.py`, `agent.py`.

## 8. EXEMPLO DE EXECUÇÃO ATUALIZADO

```
🔄 INICIANDO MIGRAÇÃO ADK

> !ls -F customer-service/
entities/
shared_libraries/
tools/
agent.py
...

📁 Criando estrutura do professor-virtual...
> !mkdir -p professor-virtual/entities
✅ 📁 Criada: professor-virtual/entities/
> !mkdir -p professor-virtual/shared_libraries
✅ 📁 Criada: professor-virtual/shared_libraries/
...

📄 Criando arquivos vazios...
> !touch professor-virtual/agent.py
✅ 📄 Criado (vazio): professor-virtual/agent.py
...

🔄 Processando: tools.py
Analisando @customer-service/tools.py e @docs/professor-virtual/implementation.py...
Escrevendo professor-virtual/tools.py...
> !echo -e "def transcrever_audio():\n  # ...lógica...\n  return" > professor-virtual/tools.py
✅ Migrado: tools.py
```

## 9. LOG FINAL OBRIGATÓRIO (FORMATO JSON)

Ao concluir TODAS as operações, você DEVE gerar um **único objeto JSON** consolidado. Não inclua nenhum outro texto na resposta final.

```json
{
  "migrationSummary": {
    "executionTimestamp": "[timestamp]",
    "sourceDirectory": "$ARGUMENTS",
    "targetDirectory": "$ARGUMENTS",
    "status": "COMPLETED",
    "totalFilesProcessed": 0
  },
  "processedFiles": [
    {
      "filePath": "entities/arquivo.py",
      "sourceFile": "$ARGUMENTS/entities/arquivo.py",
      "status": "Migrated",
      "actions": [
        "REMOVED: class Customer",
        "ADDED: class Estudante"
      ],
      "patternsPreserved": ["Pydantic BaseModel structure"]
    },
    {
      "filePath": "tools.py",
      "sourceFile": "$ARGUMENTS/tools.py",
      "status": "Migrated",
      "actions": [
        "REMOVED: function get_customer_details()",
        "ADDED: function transcrever_audio() from @docs/professor-virtual/implementation.py"
      ],
      "patternsPreserved": ["Tool return structure {status: str, data: dict}"]
    }
  ],
  "summaryStats": {
    "functionsRemoved": 0,
    "functionsAdded": 0,
    "classesModified": 0,
    "filesCreated": 0
  },
  "issuesAndPendencies": [
    "File X needs manual review.",
    "Dependency Y needs to be installed."
  ]
}
```

## 10. TRATAMENTO DE ERROS

Se qualquer comando `!` falhar:
1.  **REPORTAR**: `❌ Erro em [operação]: [descrição do erro]`
2.  **PERGUNTAR**: "Como devo proceder com este erro?"
3.  **AGUARDAR** orientação.

## 11. INICIALIZAÇÃO

Ao receber esta instrução, você deve IMEDIATAMENTE:
1.  Confirmar entendimento: `✅ AGENTE EXECUTOR ATIVADO - Modo Determinístico`
2.  Confirmar os argumentos: `Origem: $ARGUMENTS[0], Destino: $ARGUMENTS[1]`
3.  Solicitar confirmação: `Pronto para iniciar a migração. Digite 'INICIAR' para começar.`
```

---

## Arquitetura Técnica e Justificativa das Mudanças

1.  **YAML Frontmatter:** Define as permissões explícitas (`allowed-tools`) que o agente tem para interagir com o sistema. Isso é um requisito de segurança e funcionalidade do `Claude Code`.
2.  **Argumentos (`$ARGUMENTS`):** O comando agora é flexível. Você pode executá-lo com `/migrar-adk customer-service professor-virtual`, tornando-o reutilizável para outros projetos.
3.  **Comandos Explícitos (`!ls`, `!mkdir`, `!echo`):** As instruções foram traduzidas de conceitos abstratos ("Listar", "Escrever") para os comandos `bash` concretos que o `Claude Code` pode executar. O uso de `!echo -e` é especificado para lidar corretamente com as quebras de linha (`\n`).
4.  **Leitura com `@`:** O protocolo de leitura foi atualizado para usar a sintaxe `@`, que é a maneira idiomática do `Claude Code` de injetar conteúdo de arquivos no contexto.
5.  **Log Final em JSON:** O formato de saída foi alterado de Markdown para JSON. Isso transforma o log de um simples relatório em **dados estruturados**, que podem ser facilmente processados por outros scripts, usados para validação automática ou arquivados para auditoria.

## Estratégia de Validação

1.  **Salvar o Arquivo:** Crie o arquivo `.claude/commands/migrar-adk.md` no seu projeto e cole o conteúdo acima.
2.  **Executar o Comando:** Em uma sessão do `Claude Code` na raiz do seu projeto, execute o comando com os argumentos:
    ```bash
    /migrar-adk customer-service professor-virtual
    ```
3.  **Confirmar o Início:** Digite `INICIAR` quando o agente solicitar.
4.  **Observar a Execução:** Verifique se o agente está gerando os comandos `!ls`, `!mkdir`, etc., corretamente para cada fase. Aprove ou rejeite suas ações.
5.  **Verificar o Log Final:** No final do processo, o agente deve produzir um único bloco de código JSON. Copie este JSON e valide-o usando um linter de JSON para garantir que está bem-formado.

---

## Research Query

crie relatório codebase expandido, detalhado, completo que mapeie e explique absolutamente todos os arquivos do diretório "/Users/institutorecriare/VSCodeProjects/projeto_professor/professor-virtual/professor_virtual".

*Session: 8cf132c897258493528ceaaa30dba98e | Generated: 24/07/2025, 13:43:50*

### Analysis Summary

# Relatório Detalhado do Código: `professor-virtual/professor_virtual`

Este relatório detalha a estrutura e a funcionalidade de todos os arquivos dentro do diretório `professor-virtual/professor_virtual`, fornecendo uma visão abrangente de seus propósitos, componentes internos e relacionamentos.

## Visão Geral da Arquitetura

O diretório `professor-virtual/professor_virtual` encapsula a lógica central do agente "Professor Virtual". Ele é estruturado para modularizar diferentes aspectos do agente, incluindo sua configuração, prompts, definição de entidades, ferramentas e bibliotecas compartilhadas.

### Componentes Principais

*   **Agente Principal**: Definido em [agent.py](professor-virtual/professor_virtual/agent.py), este é o ponto de entrada e a orquestração principal do Professor Virtual.
*   **Configuração**: Gerencia as configurações e variáveis de ambiente para o agente, localizado em [config.py](professor-virtual/professor_virtual/config.py).
*   **Prompts**: Contém os modelos de prompt utilizados pelo agente para interagir com modelos de linguagem, em [prompts.py](professor-virtual/professor_virtual/prompts.py).
*   **Entidades**: Define as estruturas de dados ou modelos de objetos que representam conceitos chave no domínio do Professor Virtual, encontradas no diretório [entities/](professor-virtual/professor_virtual/entities).
*   **Ferramentas**: Agrupa as funcionalidades específicas que o Professor Virtual pode executar, cada uma em seu próprio módulo dentro de [tools/](professor-virtual/professor_virtual/tools).
*   **Bibliotecas Compartilhadas**: Contém utilitários e callbacks reutilizáveis que podem ser usados por diferentes partes do agente, localizadas em [shared_libraries/](professor-virtual/professor_virtual/shared_libraries).

## Detalhamento dos Arquivos e Diretórios

### Arquivos Raiz

#### `__init__.py`

*   **Propósito**: Este arquivo [__init__.py](professor-virtual/professor_virtual/__init__.py) marca o diretório `professor_virtual` como um pacote Python. Geralmente, ele pode ser usado para inicializar o pacote, definir variáveis de nível de pacote ou importar módulos para facilitar o acesso. Neste contexto, ele serve principalmente para permitir que os módulos dentro de `professor_virtual` sejam importados.
*   **Conteúdo Interno**: Vazio, indicando uma inicialização padrão do pacote.
*   **Relacionamentos Externos**: Essencial para a importação de qualquer outro módulo dentro do pacote `professor_virtual`.

#### `agent.py`

*   **Propósito**: O arquivo [agent.py](professor-virtual/professor_virtual/agent.py) é o coração do Professor Virtual, responsável por definir a lógica principal do agente, sua interação com modelos de linguagem e a orquestração das ferramentas disponíveis.
*   **Conteúdo Interno**: Contém a classe ou função principal que inicializa e executa o agente, integrando prompts, configurações e ferramentas.
*   **Relacionamentos Externos**:
    *   Depende de [config.py](professor-virtual/professor_virtual/config.py) para configurações.
    *   Utiliza prompts definidos em [prompts.py](professor-virtual/professor_virtual/prompts.py).
    *   Integra e utiliza as ferramentas definidas no diretório [tools/](professor-virtual/professor_virtual/tools).
    *   Pode fazer uso de callbacks e utilitários de [shared_libraries/](professor-virtual/professor_virtual/shared_libraries).

#### `config.py`

*   **Propósito**: O arquivo [config.py](professor-virtual/professor_virtual/config.py) é responsável por carregar e gerenciar as configurações e variáveis de ambiente necessárias para o funcionamento do Professor Virtual. Isso inclui chaves de API, URLs de serviços e outras configurações específicas do ambiente.
*   **Conteúdo Interno**: Funções ou classes para carregar variáveis de ambiente (e.g., de um arquivo `.env`) e fornecer acesso a elas.
*   **Relacionamentos Externos**: Utilizado por [agent.py](professor-virtual/professor_virtual/agent.py) e potencialmente por outras ferramentas ou bibliotecas que necessitem de configurações.

#### `prompts.py`

*   **Propósito**: O arquivo [prompts.py](professor-virtual/professor_virtual/prompts.py) armazena os modelos de prompt que o Professor Virtual utiliza para guiar as interações com os modelos de linguagem. Isso garante consistência e clareza nas instruções fornecidas ao LLM.
*   **Conteúdo Interno**: Variáveis ou funções que retornam strings formatadas, representando os prompts para diferentes cenários de uso do agente.
*   **Relacionamentos Externos**: Utilizado principalmente por [agent.py](professor-virtual/professor_virtual/agent.py) para construir as entradas para o modelo de linguagem.

### Diretório `entities/`

*   **Propósito**: O diretório [entities/](professor-virtual/professor_virtual/entities) é dedicado à definição de estruturas de dados ou modelos de objetos que representam as entidades do domínio do Professor Virtual. Isso ajuda a manter a consistência dos dados e a clareza do código.

#### `entities/__init__.py`

*   **Propósito**: Marca o diretório `entities` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

#### `entities/customer.py`

*   **Propósito**: O arquivo [customer.py](professor-virtual/professor_virtual/entities/customer.py) provavelmente define a estrutura de dados para uma entidade "cliente" ou "usuário" no contexto do Professor Virtual. Embora o nome "customer" possa parecer genérico, neste contexto educacional, pode se referir ao aluno ou usuário que interage com o Professor Virtual.
*   **Conteúdo Interno**: Definições de classes (e.g., usando `dataclasses` ou `pydantic`) com atributos como `id`, `nome`, `email`, etc., relevantes para o usuário do sistema.
*   **Relacionamentos Externos**: Pode ser utilizado por ferramentas que precisam manipular informações do usuário ou pelo agente principal para gerenciar o estado da interação.

### Diretório `shared_libraries/`

*   **Propósito**: O diretório [shared_libraries/](professor-virtual/professor_virtual/shared_libraries) contém código reutilizável que pode ser compartilhado entre diferentes partes do agente ou até mesmo entre diferentes agentes no projeto. Isso inclui utilitários e implementações de callbacks.

#### `shared_libraries/__init__.py`

*   **Propósito**: Marca o diretório `shared_libraries` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

#### `shared_libraries/callbacks.py`

*   **Propósito**: O arquivo [callbacks.py](professor-virtual/professor_virtual/shared_libraries/callbacks.py) provavelmente define interfaces ou classes base para callbacks que podem ser acionados em diferentes estágios da execução do agente (e.g., antes de uma ferramenta ser chamada, depois de uma ferramenta, antes do agente iniciar).
*   **Conteúdo Interno**: Definições de classes abstratas ou interfaces para callbacks, que são então implementadas em subdiretórios específicos.
*   **Relacionamentos Externos**: As implementações específicas de callbacks nos subdiretórios dependem dessas definições. O agente principal pode registrar e chamar esses callbacks.

#### Diretório `shared_libraries/callbacks/`

*   **Propósito**: Este diretório [shared_libraries/callbacks/](professor-virtual/professor_virtual/shared_libraries/callbacks) agrupa as implementações concretas de diferentes tipos de callbacks.

##### `shared_libraries/callbacks/__init__.py`

*   **Propósito**: Marca o diretório `callbacks` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

##### Diretório `shared_libraries/callbacks/after_tool/`

*   **Propósito**: Contém callbacks que são executados após a conclusão de uma ferramenta.

###### `shared_libraries/callbacks/after_tool/__init__.py`

*   **Propósito**: Marca o diretório `after_tool` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

###### `shared_libraries/callbacks/after_tool/after_tool_callback.py`

*   **Propósito**: O arquivo [after_tool_callback.py](professor-virtual/professor_virtual/shared_libraries/callbacks/after_tool/after_tool_callback.py) implementa a lógica específica para um callback que é executado após uma ferramenta ter sido utilizada pelo agente.
*   **Conteúdo Interno**: Uma classe que herda de uma interface de callback (provavelmente definida em [callbacks.py](professor-virtual/professor_virtual/shared_libraries/callbacks.py)) e contém o método para ser executado.
*   **Relacionamentos Externos**: Chamado pelo agente principal após a execução de uma ferramenta.

##### Diretório `shared_libraries/callbacks/before_agent/`

*   **Propósito**: Contém callbacks que são executados antes do agente iniciar sua execução principal.

###### `shared_libraries/callbacks/before_agent/__init__.py`

*   **Propósito**: Marca o diretório `before_agent` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

###### `shared_libraries/callbacks/before_agent/before_agent_callback.py`

*   **Propósito**: O arquivo [before_agent_callback.py](professor-virtual/professor_virtual/shared_libraries/callbacks/before_agent/before_agent_callback.py) implementa a lógica para um callback que é executado antes do agente iniciar seu processamento.
*   **Conteúdo Interno**: Uma classe de callback com lógica de pré-processamento.
*   **Relacionamentos Externos**: Chamado pelo agente principal antes de sua execução.

##### Diretório `shared_libraries/callbacks/before_tool/`

*   **Propósito**: Contém callbacks que são executados antes de uma ferramenta ser invocada.

###### `shared_libraries/callbacks/before_tool/__init__.py`

*   **Propósito**: Marca o diretório `before_tool` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

###### `shared_libraries/callbacks/before_tool/before_tool_callback.py`

*   **Propósito**: O arquivo [before_tool_callback.py](professor-virtual/professor_virtual/shared_libraries/callbacks/before_tool/before_tool_callback.py) implementa a lógica para um callback que é executado imediatamente antes de uma ferramenta ser chamada.
*   **Conteúdo Interno**: Uma classe de callback com lógica de pré-execução de ferramenta.
*   **Relacionamentos Externos**: Chamado pelo agente principal antes de invocar uma ferramenta.

##### Diretório `shared_libraries/callbacks/lowercase_value/`

*   **Propósito**: Contém um callback específico para converter valores para minúsculas.

###### `shared_libraries/callbacks/lowercase_value/__init__.py`

*   **Propósito**: Marca o diretório `lowercase_value` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

###### `shared_libraries/callbacks/lowercase_value/lowercase_value.py`

*   **Propósito**: O arquivo [lowercase_value.py](professor-virtual/professor_virtual/shared_libraries/callbacks/lowercase_value/lowercase_value.py) implementa um callback que pode ser usado para normalizar entradas, convertendo-as para minúsculas.
*   **Conteúdo Interno**: Uma classe de callback que realiza a conversão de string para minúsculas.
*   **Relacionamentos Externos**: Pode ser aplicado a entradas de ferramentas ou a outros dados que necessitem de normalização.

##### Diretório `shared_libraries/callbacks/rate_limit_callback/`

*   **Propósito**: Contém um callback para gerenciar limites de taxa.

###### `shared_libraries/callbacks/rate_limit_callback/__init__.py`

*   **Propósito**: Marca o diretório `rate_limit_callback` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

###### `shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py`

*   **Propósito**: O arquivo [rate_limit_callback.py](professor-virtual/professor_virtual/shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py) implementa um callback para impor limites de taxa em chamadas de API ou outras operações, prevenindo o uso excessivo de recursos.
*   **Conteúdo Interno**: Lógica para controlar a frequência de chamadas.
*   **Relacionamentos Externos**: Pode ser integrado a ferramentas ou ao agente principal para gerenciar o consumo de recursos externos.

##### Diretório `shared_libraries/callbacks/validate_customer_id/`

*   **Propósito**: Contém um callback para validar IDs de clientes.

###### `shared_libraries/callbacks/validate_customer_id/__init__.py`

*   **Propósito**: Marca o diretório `validate_customer_id` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

###### `shared_libraries/callbacks/validate_customer_id/validate_customer_id_callback.py`

*   **Propósito**: O arquivo [validate_customer_id_callback.py](professor-virtual/professor_virtual/shared_libraries/callbacks/validate_customer_id/validate_customer_id_callback.py) implementa um callback para validar o formato ou a existência de IDs de clientes.
*   **Conteúdo Interno**: Lógica de validação para IDs de clientes.
*   **Relacionamentos Externos**: Pode ser usado por ferramentas que recebem ou processam IDs de clientes.

### Diretório `tools/`

*   **Propósito**: O diretório [tools/](professor-virtual/professor_virtual/tools) contém as definições e implementações das ferramentas que o Professor Virtual pode utilizar para realizar ações específicas. Cada subdiretório representa uma ferramenta distinta.

#### `tools/__init__.py`

*   **Propósito**: Marca o diretório `tools` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

#### `tools/tools.py`

*   **Propósito**: O arquivo [tools.py](professor-virtual/professor_virtual/tools/tools.py) pode atuar como um módulo agregador, importando e expondo todas as ferramentas disponíveis para o agente principal. Alternativamente, pode conter funções utilitárias genéricas relacionadas a ferramentas.
*   **Conteúdo Interno**: Pode conter uma lista ou dicionário de todas as ferramentas, ou funções auxiliares para o registro e gerenciamento de ferramentas.
*   **Relacionamentos Externos**: Utilizado por [agent.py](professor-virtual/professor_virtual/agent.py) para descobrir e carregar as ferramentas.

#### Diretório `tools/analisar_imagem_educacional/`

*   **Propósito**: Contém a ferramenta para analisar imagens educacionais.

##### `tools/analisar_imagem_educacional/__init__.py`

*   **Propósito**: Marca o diretório `analisar_imagem_educacional` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

##### `tools/analisar_imagem_educacional/analisar_imagem_educacional.py`

*   **Propósito**: O arquivo [analisar_imagem_educacional.py](professor-virtual/professor_virtual/tools/analisar_imagem_educacional/analisar_imagem_educacional.py) implementa a funcionalidade para o Professor Virtual analisar o conteúdo de imagens com foco educacional. Isso pode envolver reconhecimento de objetos, texto ou conceitos visuais.
*   **Conteúdo Interno**: Funções ou classes que interagem com APIs de visão computacional ou modelos de IA para processar imagens.
*   **Relacionamentos Externos**: Chamado pelo agente principal quando a análise de imagem é necessária. Pode depender de serviços externos ou bibliotecas de processamento de imagem.

#### Diretório `tools/analisar_necessidade_visual/`

*   **Propósito**: Contém a ferramenta para analisar necessidades visuais.

##### `tools/analisar_necessidade_visual/__init__.py`

*   **Propósito**: Marca o diretório `analisar_necessidade_visual` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

##### `tools/analisar_necessidade_visual/analisar_necessidade_visual.py`

*   **Propósito**: O arquivo [analisar_necessidade_visual.py](professor-virtual/professor_virtual/tools/analisar_necessidade_visual/analisar_necessidade_visual.py) implementa uma ferramenta para o Professor Virtual avaliar ou identificar necessidades visuais específicas de um usuário ou contexto. Isso pode estar relacionado a acessibilidade ou preferências de exibição.
*   **Conteúdo Interno**: Lógica para interpretar entradas e determinar requisitos visuais.
*   **Relacionamentos Externos**: Chamado pelo agente principal para adaptar a saída ou a interação com base nas necessidades visuais.

#### Diretório `tools/gerar_audio_tts/`

*   **Propósito**: Contém a ferramenta para gerar áudio via Text-to-Speech (TTS).

##### `tools/gerar_audio_tts/__init__.py`

*   **Propósito**: Marca o diretório `gerar_audio_tts` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

##### `tools/gerar_audio_tts/gerar_audio_tts.py`

*   **Propósito**: O arquivo [gerar_audio_tts.py](professor-virtual/professor_virtual/tools/gerar_audio_tts/gerar_audio_tts.py) implementa a funcionalidade de Text-to-Speech (TTS), permitindo que o Professor Virtual converta texto em fala.
*   **Conteúdo Interno**: Funções ou classes que interagem com APIs de TTS (e.g., Google Cloud Text-to-Speech, Amazon Polly) para sintetizar áudio a partir de texto.
*   **Relacionamentos Externos**: Chamado pelo agente principal quando uma resposta de áudio é necessária.

#### Diretório `tools/transcrever_audio/`

*   **Propósito**: Contém a ferramenta para transcrever áudio.

##### `tools/transcrever_audio/__init__.py`

*   **Propósito**: Marca o diretório `transcrever_audio` como um pacote Python.
*   **Conteúdo Interno**: Vazio.

##### `tools/transcrever_audio/transcrever_audio.py`

*   **Propósito**: O arquivo [transcrever_audio.py](professor-virtual/professor_virtual/tools/transcrever_audio/transcrever_audio.py) implementa a funcionalidade de Speech-to-Text (STT), permitindo que o Professor Virtual transcreva áudio em texto.
*   **Conteúdo Interno**: Funções ou classes que interagem com APIs de STT (e.g., Google Cloud Speech-to-Text, OpenAI Whisper) para converter fala em texto.
*   **Relacionamentos Externos**: Chamado pelo agente principal quando a entrada de áudio precisa ser processada.

---

## Research Query

faltaram vários arquivos além de não ter criado o diagrama mermaid. Refaça com mais detalhemento.

*Session: da8d32d6d00a59906646afb7a141d703 | Generated: 24/07/2025, 13:46:28*

### Analysis Summary

# Customer Service Codebase Analysis

This report details the architecture and components of the **Customer Service** module, providing a structured overview of its functionalities, internal organization, and inter-component relationships.

## High-Level Architecture

The **Customer Service** module, located at [customer-service/](customer-service/), is designed to automate and assist with customer interactions. It primarily functions as an agent-based system, leveraging various tools and shared libraries to process customer requests, access information, and perform actions. Its core components include an **agent** responsible for orchestrating tasks, **prompts** for guiding the agent's behavior, **entities** for data modeling, **shared libraries** for common functionalities like callbacks, and a collection of specialized **tools** for interacting with external systems or performing specific operations.

## Core Components

### Agent Orchestration

The central orchestrator of the customer service interactions is defined in [customer-service/customer_service/agent.py](customer-service/customer_service/agent.py). This file likely contains the main logic for the agent, including how it receives input, decides which tools to use, and generates responses.

### Configuration Management

Module-specific configurations are managed in [customer-service/customer_service/config.py](customer-service/customer_service/config.py). This file typically holds settings, API keys, or other parameters necessary for the module's operation.

### Prompt Definitions

The conversational prompts and instructions that guide the agent's behavior and responses are defined in [customer-service/customer_service/prompts.py](customer-service/customer_service/prompts.py). These prompts are crucial for shaping the agent's personality and interaction style.

## Data Entities

The **entities** directory, located at [customer-service/customer_service/entities/](customer-service/customer_service/entities/), defines the data structures or models used within the customer service domain.

### Customer Entity

The primary entity representing customer information is defined in [customer-service/customer_service/entities/customer.py](customer-service/customer_service/entities/customer.py). This file likely contains the class or data structure for `Customer` objects, including their attributes and methods.

## Shared Libraries

The **shared_libraries** directory, found at [customer-service/customer_service/shared_libraries/](customer-service/customer_service/shared_libraries/), houses reusable components and utilities that can be shared across different parts of the customer service module or even other agents.

### Callbacks

The **callbacks** sub-directory, located at [customer-service/customer_service/shared_libraries/callbacks/](customer-service/customer_service/shared_libraries/callbacks/), contains various callback functions that can be triggered at different stages of the agent's execution. The main entry point for callbacks is [customer-service/customer_service/shared_libraries/callbacks.py](customer-service/customer_service/shared_libraries/callbacks.py).

Specific callback implementations include:

*   **After Tool Callback**: [customer-service/customer_service/shared_libraries/callbacks/after_tool/after_tool_callback.py](customer-service/customer_service/shared_libraries/callbacks/after_tool/after_tool_callback.py) - Executed after a tool has been used.
*   **Before Agent Callback**: [customer-service/customer_service/shared_libraries/callbacks/before_agent/before_agent_callback.py](customer-service/customer_service/shared_libraries/callbacks/before_agent/before_agent_callback.py) - Executed before the agent starts processing.
*   **Before Tool Callback**: [customer-service/customer_service/shared_libraries/callbacks/before_tool/before_tool_callback.py](customer-service/customer_service/shared_libraries/callbacks/before_tool/before_tool_callback.py) - Executed before a tool is invoked.
*   **Lowercase Value Callback**: [customer-service/customer_service/shared_libraries/callbacks/lowercase_value/lowercase_value.py](customer-service/customer_service/shared_libraries/callbacks/lowercase_value/lowercase_value.py) - A utility callback for converting values to lowercase.
*   **Rate Limit Callback**: [customer-service/customer_service/shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py](customer-service/customer_service/shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py) - Handles rate limiting for tool usage or API calls.
*   **Validate Customer ID Callback**: [customer-service/customer_service/shared_libraries/callbacks/validate_customer_id/validate_customer_id_callback.py](customer-service/customer_service/shared_libraries/callbacks/validate_customer_id/validate_customer_id_callback.py) - Validates customer identification.

## Tools

The **tools** directory, located at [customer-service/customer_service/tools/](customer-service/customer_service/tools/), contains a collection of specialized functions or modules that the agent can utilize to perform specific actions or retrieve information. The main entry point for tool definitions is [customer-service/customer_service/tools/tools.py](customer-service/customer_service/tools/tools.py).

Each sub-directory within `tools/` represents a distinct tool:

*   **Access Cart Information**: [customer-service/customer_service/tools/access_cart_information/access_cart_information.py](customer-service/customer_service/tools/access_cart_information/access_cart_information.py) - Provides functionality to retrieve details about a customer's shopping cart.
*   **Approve Discount**: [customer-service/customer_service/tools/approve_discount/approve_discount.py](customer-service/customer_service/tools/approve_discount/approve_discount.py) - Enables the agent to approve discounts for customers.
*   **Check Product Availability**: [customer-service/customer_service/tools/check_product_availability/check_product_availability.py](customer-service/customer_service/tools/check_product_availability/check_product_availability.py) - Allows checking the stock or availability of products.
*   **Generate QR Code**: [customer-service/customer_service/tools/generate_qr_code/generate_qr_code.py](customer-service/customer_service/tools/generate_qr_code/generate_qr_code.py) - Generates QR codes for various purposes.
*   **Get Available Planting Times**: [customer-service/customer_service/tools/get_available_planting_times/get_available_planting_times.py](customer-service/customer_service/tools/get_available_planting_times/get_available_planting_times.py) - Retrieves information about available planting schedules.
*   **Get Product Recommendations**: [customer-service/customer_service/tools/get_product_recommendations/get_product_recommendations.py](customer-service/customer_service/tools/get_product_recommendations/get_product_recommendations.py) - Provides product suggestions based on customer preferences or history.
*   **Modify Cart**: [customer-service/customer_service/tools/modify_cart/modify_cart.py](customer-service/customer_service/tools/modify_cart/modify_cart.py) - Allows modifications to the customer's shopping cart, such as adding or removing items.
*   **Schedule Planting Service**: [customer-service/customer_service/tools/schedule_planting_service/schedule_planting_service.py](customer-service/customer_service/tools/schedule_planting_service/schedule_planting_service.py) - Facilitates scheduling services related to planting.
*   **Send Call Companion Link**: [customer-service/customer_service/tools/send_call_companion_link/send_call_companion_link.py](customer-service/customer_service/tools/send_call_companion_link/send_call_companion_link.py) - Sends a link to a companion application or resource during a call.
*   **Send Care Instructions**: [customer-service/customer_service/tools/send_care_instructions/send_care_instructions.py](customer-service/customer_service/tools/send_care_instructions/send_care_instructions.py) - Provides functionality to send care instructions for products or services.
*   **Sync Ask For Approval**: [customer-service/customer_service/tools/sync_ask_for_approval/sync_ask_for_approval.py](customer-service/customer_service/tools/sync_ask_for_approval/sync_ask_for_approval.py) - Handles synchronous requests for approval.
*   **Update Salesforce CRM**: [customer-service/customer_service/tools/update_salesforce_crm/update_salesforce_crm.py](customer-service/customer_service/tools/update_salesforce_crm/update_salesforce_crm.py) - Integrates with Salesforce CRM to update customer records.

