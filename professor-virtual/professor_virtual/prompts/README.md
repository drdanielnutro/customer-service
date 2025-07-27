# Sistema de Prompts do Professor Virtual

## Visão Geral

Este módulo implementa o sistema de **Instruction Providers** do Professor Virtual, uma abordagem dinâmica para geração de prompts que permite personalização baseada no contexto da sessão. O sistema utiliza o padrão do Google Agent Development Kit (ADK) para criar instruções adaptativas que orientam o comportamento do agente.

## Arquitetura do Sistema

### Fluxo de Dados

```
agent.py
    ↓
prompts/__init__.py
    ↓
prompts.py
    ↓
Instruction Providers (funções)
    ↓
String de instrução personalizada
```

### Componentes Principais

1. **Instruction Providers**: Funções que geram instruções dinamicamente
2. **Constantes de Exportação**: INSTRUCTION e GLOBAL_INSTRUCTION
3. **Dicionário de Providers**: Mapeamento para acesso facilitado

## Instruction Providers Disponíveis

### 1. professor_instruction_provider

**Propósito**: Gera a instrução principal que define o comportamento do Professor Virtual.

**Personalização baseada em contexto**:
- Nome do aluno (`user:name`)
- Série escolar (`user:serie_escolar`)

**Estrutura da instrução gerada**:
- Missão principal e personalidade
- Regras detalhadas para uso de ferramentas
- Diretrizes para formatação de respostas
- Abordagem pedagógica

**Exemplo de uso**:
```python
instruction = professor_instruction_provider(context)
# Retorna: "Você é o Professor Virtual... falando com João que está na 5ª série."
```

### 2. erro_instruction_provider

**Propósito**: Gera mensagens amigáveis para situações de erro.

**Tipos de erro suportados**:
- `entender_audio`: Problemas na transcrição de áudio
- `processar_imagem`: Falhas no processamento de imagem
- Outros erros genéricos

**Características**:
- Linguagem apropriada para crianças
- Tom encorajador
- Sugestões práticas de solução

### 3. boas_vindas_provider

**Propósito**: Cria mensagens de boas-vindas personalizadas.

**Comportamento**:
- Primeira interação: Apresentação completa
- Interações subsequentes: Saudação personalizada com nome

## Como Funciona

### 1. Contexto (ReadonlyContext)

O ADK passa um objeto `ReadonlyContext` que contém:
- Estado da sessão
- Informações do usuário
- Variáveis temporárias

### 2. Geração Dinâmica

```python
def professor_instruction_provider(context: ReadonlyContext) -> str:
    # Extrai informações do contexto
    user_name = context.state.get("user:name", "aluno(a)")
    
    # Gera instrução personalizada
    instruction = f"Você está falando com {user_name}..."
    
    return instruction
```

### 3. Integração com o Agente

```python
from .prompts import INSTRUCTION

agent = Agent(
    instruction=INSTRUCTION,  # Usa o provider dinâmico
    # ... outras configurações
)
```

## Adicionando Novos Providers

### Passo 1: Criar a função provider

```python
def meu_provider(context: ReadonlyContext) -> str:
    """Descrição do que o provider faz."""
    # Lógica de geração
    return "Instrução gerada"
```

### Passo 2: Registrar no dicionário

```python
INSTRUCTION_PROVIDERS = {
    "professor_instructions": professor_instruction_provider,
    "meu_provider": meu_provider,  # Novo provider
}
```

### Passo 3: Exportar se necessário

Adicione ao `__init__.py`:
```python
from .prompts import meu_provider

__all__ = [..., "meu_provider"]
```

## Exemplos de Uso

### Uso Básico

```python
from professor_virtual.prompts import INSTRUCTION

# O agente usará automaticamente o provider dinâmico
agent = Agent(instruction=INSTRUCTION)
```

### Acesso Direto a Providers

```python
from professor_virtual.prompts import INSTRUCTION_PROVIDERS

# Para mensagens de erro
erro_msg = INSTRUCTION_PROVIDERS["erro_processamento"](context)

# Para boas-vindas
welcome = INSTRUCTION_PROVIDERS["boas_vindas"](context)
```

### Testando Providers

```python
# Mock de contexto para testes
class MockContext:
    def __init__(self):
        self.state = {"user:name": "Maria", "user:serie_escolar": "4ª série"}

context = MockContext()
instruction = professor_instruction_provider(context)
print(instruction)
```

## Integração com ADK

### Padrão de Instruction Providers

O Google ADK suporta dois tipos de instruções:

1. **Estáticas**: Strings fixas (usado em `GLOBAL_INSTRUCTION`)
2. **Dinâmicas**: Funções que retornam strings (usado em `INSTRUCTION`)

### Vantagens da Abordagem Dinâmica

- **Personalização**: Adapta-se ao contexto do usuário
- **Flexibilidade**: Comportamento muda baseado no estado
- **Manutenibilidade**: Lógica centralizada em funções
- **Testabilidade**: Providers podem ser testados isoladamente

## Melhores Práticas

1. **Mantenha providers focados**: Cada provider deve ter uma responsabilidade clara
2. **Use contexto com segurança**: Sempre forneça valores padrão com `.get()`
3. **Documente comportamentos**: Explique quando e como cada provider é usado
4. **Teste edge cases**: Verifique comportamento com contexto vazio ou incompleto
5. **Evite lógica complexa**: Providers devem gerar strings, não executar regras de negócio

## Estrutura de Arquivos

```
prompts/
├── __init__.py      # Exportações públicas do módulo
├── prompts.py       # Implementação dos providers
└── README.md        # Esta documentação
```

## Troubleshooting

### Provider não está sendo chamado
- Verifique se está usando `INSTRUCTION` (função) e não uma string
- Confirme que o import está correto

### Erro de contexto
- Certifique-se de usar `.get()` com valores padrão
- Valide que o contexto contém as chaves esperadas

### Personalização não funciona
- Debug: imprima o contexto recebido
- Verifique se o estado está sendo populado corretamente