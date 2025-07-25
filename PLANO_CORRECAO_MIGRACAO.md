# PLANO DE CORREÇÃO - MIGRAÇÃO ADK

**Data de Análise**: 2025-07-25  
**Diretório Origem**: `/customer-service`  
**Diretório Destino**: `/professor-virtual`  
**Status Geral**: MIGRAÇÃO COM INCONSISTÊNCIAS

## 🔴 INCONSISTÊNCIAS CRÍTICAS

### 1. pyproject.toml - ERRO DE AUTORIA
**Arquivo**: `/professor-virtual/pyproject.toml`  
**Linha**: 5  
**Problema**: O campo `authors` não foi personalizado corretamente.

**Estado Atual**:
```toml
authors = ["Google Educational Team <education@example.com>"]
```

**Correção Necessária**:
```toml
authors = ["Instituto Recriare <contato@institutorecriare.com>"]
```

**Justificativa**: O arquivo deve refletir a autoria real do projeto, não uma referência genérica.

### 2. .gitignore - REFERÊNCIA INCORRETA
**Arquivo**: `/professor-virtual/.gitignore`  
**Linha**: 2  
**Problema**: Ainda contém referência ao arquivo wheel do customer-service.

**Estado Atual**:
```
customer_service-0.1.0-py3-none-any.whl
```

**Correção Necessária**:
```
professor_virtual-0.1.0-py3-none-any.whl
```

**Justificativa**: O arquivo wheel gerado terá o nome do novo projeto.

### 3. README.md - DOCUMENTAÇÃO INCOMPLETA
**Arquivo**: `/professor-virtual/README.md`  
**Problema**: O README está muito simplificado e não segue a estrutura especificada no AGENTS.md.

**Estrutura Necessária**:
1. **Título**: Professor Virtual - Assistente Educacional
2. **Visão Geral**: Descrição detalhada do agente educacional
3. **Ferramentas**: Lista completa das ferramentas disponíveis
4. **Instalação**: Instruções passo a passo
5. **Uso**: Como executar o agente
6. **Avaliação**: Como executar os testes
7. **Configuração**: Referência ao config.py
8. **Deployment**: Instruções para Google Agent Engine

## ✅ VERIFICAÇÕES APROVADAS

1. **.env.example**: Corretamente traduzido para português
2. **Diretórios auxiliares**: Todos criados conforme especificado
3. **deployment/deploy.py**: Adaptado corretamente para professor_virtual
4. **Estrutura de pastas**: Mantida conforme o padrão ADK

## 📋 AÇÕES DE CORREÇÃO

### Prioridade ALTA
1. [ ] Atualizar o campo `authors` no pyproject.toml
2. [ ] Reescrever o README.md com estrutura completa

### Prioridade MÉDIA
3. [ ] Corrigir referência no .gitignore

### Prioridade BAIXA
4. [ ] Verificar se há outras referências hardcoded que precisam ser atualizadas

## 💡 RECOMENDAÇÕES ADICIONAIS

1. **Testes de Integração**: Após as correções, executar `poetry install` para verificar se todas as dependências estão corretas.

2. **Validação da Documentação**: O README deve incluir exemplos práticos de uso do Professor Virtual, demonstrando as ferramentas educacionais.

3. **Revisão de Configurações**: Verificar se o arquivo `config.py` está usando os nomes corretos do projeto em todas as referências.

## 🚀 PRÓXIMOS PASSOS

1. Execute as correções listadas acima
2. Rode os testes unitários: `pytest tests/unit`
3. Valide a avaliação: `pytest eval`
4. Confirme que o deployment funciona: `cd deployment && python deploy.py`

---

**Nota**: Este plano foi gerado após análise detalhada da migração ADK. Todas as inconsistências foram identificadas comparando os arquivos originais com as especificações do arquivo AGENTS.md.