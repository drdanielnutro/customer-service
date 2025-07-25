## Fonte da Verdade – Cymbal Home & Garden Customer Service Agent (v0.1.0 - Single Agent Pattern)

[NOTA: Este documento foi reconstruído através de engenharia reversa do código implementado]

Este documento descreve o comportamento e os fluxos do agente Project Pro, baseado em análise do código e arquitetura implementada.

# Fluxo de Interação Conversacional - Project Pro (Customer Service Agent)

## Visão Geral

O agente "Project Pro" é um assistente de IA especializado em atendimento ao cliente para a Cymbal Home & Garden, uma loja de varejo especializada em jardinagem, produtos para casa e serviços relacionados. O agente foi projetado para fornecer uma experiência de compra personalizada e sem atritos, combinando capacidades conversacionais avançadas com integração de ferramentas específicas do domínio.

A análise revela um foco claro em:
- Personalização baseada em histórico do cliente
- Identificação visual de produtos (plantas) via vídeo
- Gestão completa do ciclo de compra
- Promoção inteligente de serviços adicionais

## Arquitetura Descoberta

### Estrutura de Agentes

**Tipo:** Single Agent (google.adk.Agent)
- **Nome:** customer_service_agent
- **Modelo LLM:** gemini-2.5-flash  
- **Padrão:** Agente único com múltiplas ferramentas
- **Abordagem:** Tool-based interaction com callbacks avançados

### Componentes Identificados

#### **Agentes:**
- **root_agent** (`customer_service/agent.py`) - Agente principal e único que gerencia toda a interação
  - Utiliza instruções globais e específicas
  - Integra 12 ferramentas especializadas
  - Implementa 4 tipos de callbacks para controle de fluxo

#### **Tools:** 
1. **send_call_companion_link** (`customer_service/tools/send_call_companion_link/send_call_companion_link.py`) - Inicia sessão de vídeo para identificação visual
2. **approve_discount** (`customer_service/tools/approve_discount/approve_discount.py`) - Aprova descontos automaticamente (limite: 10%)
3. **sync_ask_for_approval** (`customer_service/tools/sync_ask_for_approval/sync_ask_for_approval.py`) - Solicita aprovação gerencial para descontos maiores
4. **update_salesforce_crm** (`customer_service/tools/update_salesforce_crm/update_salesforce_crm.py`) - Atualiza registros do cliente no CRM
5. **access_cart_information** (`customer_service/tools/access_cart_information/access_cart_information.py`) - Recupera conteúdo atual do carrinho
6. **modify_cart** (`customer_service/tools/modify_cart/modify_cart.py`) - Adiciona/remove itens do carrinho
7. **get_product_recommendations** (`customer_service/tools/get_product_recommendations/get_product_recommendations.py`) - Recomenda produtos baseados no tipo de planta
8. **check_product_availability** (`customer_service/tools/check_product_availability/check_product_availability.py`) - Verifica disponibilidade em estoque
9. **schedule_planting_service** (`customer_service/tools/schedule_planting_service/schedule_planting_service.py`) - Agenda serviços de plantio
10. **get_available_planting_times** (`customer_service/tools/get_available_planting_times/get_available_planting_times.py`) - Lista horários disponíveis
11. **send_care_instructions** (`customer_service/tools/send_care_instructions/send_care_instructions.py`) - Envia instruções de cuidado por email/SMS
12. **generate_qr_code** (`customer_service/tools/generate_qr_code/generate_qr_code.py`) - Gera códigos QR com desconto para fidelização

#### **Modelos:**
- **LLM Principal:** gemini-2.5-flash (Vertex AI)
- **Configuração:** Via variáveis de ambiente com fallback para valores padrão (`customer_service/config.py`)

#### **Callbacks Customizados:**
1. **rate_limit_callback** (`customer_service/shared_libraries/callbacks/rate_limit_callback/rate_limit_callback.py`) - Controle de taxa (10 RPM)
2. **before_agent** (`customer_service/shared_libraries/callbacks/before_agent/before_agent_callback.py`) - Carrega perfil do cliente na sessão
3. **before_tool** (`customer_service/shared_libraries/callbacks/before_tool/before_tool_callback.py`) - Validação de customer_id e regras de negócio
4. **after_tool** (`customer_service/shared_libraries/callbacks/after_tool/after_tool_callback.py`) - Aplicação determinística de descontos aprovados

## Fluxo de Interação Reconstruído

### 1. Inicialização da Sessão
```
[before_agent_callback]
  └─> Carrega perfil do cliente Alex Johnson (ID: 123)
  └─> Injeta dados no estado da sessão
  └─> Personaliza contexto global com histórico
```

### 2. Fluxo Principal de Conversação

#### Fase de Boas-Vindas
- Reconhecimento do cliente pelo nome
- Menção ao tempo como cliente (2 anos)
- Referência ao carrinho atual se houver itens

**Arquivos principais:**
- Agent: `customer_service/agent.py`
- Config: `customer_service/config.py`
- Prompts: `customer_service/prompts.py`

#### Fase de Identificação de Produtos
1. Cliente descreve planta vagamente
2. Agente sugere compartilhamento de vídeo
3. Ativa `send_call_companion_link`
4. Identifica planta visualmente
5. Busca recomendações específicas

#### Fase de Recomendação e Venda
1. `get_product_recommendations` baseado na planta identificada
2. Considera localização (Las Vegas, NV) para produtos adequados
3. `access_cart_information` antes de sugerir
4. Oferece alternativas melhores se aplicável
5. `modify_cart` com confirmação do cliente

#### Fase de Upselling
- Sugere serviços profissionais de plantio
- Oferece descontos competitivos:
  - Auto-aprovação até 10%
  - Aprovação gerencial para valores maiores
- Agenda serviços se aceitos

#### Fase de Finalização
- Envia instruções de cuidado
- Gera QR code de desconto futuro
- Atualiza CRM com detalhes da interação

## Comportamentos Observados

### Personalização Inteligente
- Sistema pré-carrega dados completos do cliente
- Histórico de compras influencia recomendações
- Preferências de comunicação respeitadas

### Gestão de Descontos em Camadas
```python
if discount <= 10:
    → approve_discount() [auto-aprovado]
else:
    → sync_ask_for_approval() [requer gerente]
```

### Validação Rigorosa
- Todas as operações validam customer_id
- Callbacks interceptam e corrigem dados
- Proteção contra manipulação de descontos

### Multimodalidade Nativa
- Integração de vídeo para identificação visual
- Processamento de texto e imagem
- Resposta contextualizada baseada em análise visual

## Inferências e Descobertas

### Decisões de Design Aparentes

1. **Estado Pré-carregado vs Autenticação**
   - Cliente já "autenticado" no início
   - Simula ambiente pós-login
   - Foco na experiência, não na segurança

2. **Ferramentas Mockadas**
   - Todas as ferramentas retornam dados simulados
   - Preparado para integração real futura
   - Permite desenvolvimento independente

3. **Arquitetura de Callbacks Defensiva**
   - Múltiplas camadas de validação
   - Separação entre decisão (agente) e execução (callbacks)
   - Proteção contra prompt injection
   - Callbacks centralizados em: `customer_service/shared_libraries/callbacks/`

4. **Rate Limiting Inteligente**
   - Implementado via callback antes do modelo
   - 10 requisições por minuto
   - Reset automático após 60 segundos

### Casos de Uso Implícitos

1. **Atendimento Pós-Compra Física**
   - Cliente comprou plantas na loja
   - Esqueceu itens complementares
   - Precisa fazer pedido para retirada

2. **Identificação Visual de Produtos**
   - Plantas com etiquetas genéricas
   - Necessidade de cuidados específicos
   - Venda de produtos adequados

3. **Fidelização através de Serviços**
   - Upsell de serviços profissionais
   - Descontos estratégicos
   - QR codes para próxima compra

4. **Competição com Concorrentes**
   - Sistema preparado para "price match"
   - Flexibilidade em descontos
   - Foco em retenção

### Limitações Identificadas

1. **Dados Mockados**
   - Carrinho não persiste mudanças
   - Produtos sempre disponíveis
   - Agendamentos não são reais

2. **Cliente Único**
   - Hardcoded para customer_id "123" (em `customer_service/entities/customer.py`)
   - Não há mecanismo de troca de contexto
   - Assume sessão já autenticada

3. **Integração Limitada**
   - Sem backends reais
   - CRM updates são no-op
   - Vídeo é simulado

**Nota:** Todas as ferramentas estão organizadas em `customer_service/tools/` com cada uma em seu próprio subdiretório.

## Notas de Engenharia Reversa

### Confiança das Inferências

**Alta confiança:**
- Arquitetura single-agent com ferramentas
- Lista completa de 12 ferramentas e seus propósitos
- Fluxo de callbacks e validações
- Modelo LLM utilizado (gemini-2.5-flash)
- Personalização baseada em perfil pré-carregado
- Rate limiting de 10 RPM

**Média confiança:**
- Casos de uso específicos (inferidos de ferramentas e prompts)
- Estratégia de upselling (baseada em instruções)
- Integração multimodal via vídeo
- Processo de identificação visual de plantas

**Baixa confiança:**
- Detalhes de implementação real dos backends
- Métricas de sucesso do agente
- Processos de treinamento ou fine-tuning
- Estratégias de fallback em produção

### Lacunas Identificadas

1. **Autenticação e Segurança**
   - Não há código de autenticação visível
   - Assumido que acontece externamente
   - Sem tratamento de múltiplos usuários

2. **Persistência Real**
   - Todas as operações são mockadas
   - Não há código de integração real
   - Estado não persiste entre sessões

3. **Tratamento de Erros Avançado**
   - Fallbacks limitados
   - Sem retry logic visível
   - Dependência do LLM para recuperação

4. **Métricas e Observabilidade**
   - Logging básico presente
   - Sem instrumentação para produção
   - Ausência de dashboards ou alertas