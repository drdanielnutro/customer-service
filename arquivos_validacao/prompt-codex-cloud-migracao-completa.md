# Prompt para Codex Cloud - Completar Migração ADK

## Contexto

Você já criou a estrutura interna do Professor Virtual em `professor-virtual/professor_virtual/` através de engenharia reversa do projeto `customer-service`. Porém, faltam os arquivos de configuração do nível raiz e os diretórios auxiliares (deployment, eval, tests).

## Tarefa

Execute o comando `/migrar-adk` com o arquivo AGENTS.md atualizado para completar a migração, focando especificamente nas FASES 0 e 5 que foram adicionadas.

## Comando a Executar

```bash
/migrar-adk customer-service professor-virtual
```

## Instruções Específicas

1. **FASE 0** - Migre os arquivos de configuração do nível raiz:
   - `pyproject.toml` - Adapte para "professor-virtual" 
   - `README.md` - Crie nova documentação educacional
   - `.env.example` - Copie com comentários adaptados
   - `.gitignore` - Copie integralmente

2. **FASE 5** - Crie os diretórios auxiliares:
   - `deployment/` com `deploy.py` adaptado
   - `eval/` com estrutura de testes educacionais
   - `tests/` com testes unitários para ferramentas

3. **Importante**: 
   - A estrutura `professor_virtual/` já existe e não deve ser recriada
   - Foque apenas nos arquivos do nível raiz e diretórios auxiliares
   - Use o conteúdo de `desenvolvedor/` como referência para adaptações

## Resultado Esperado

Após executar o comando, o diretório `professor-virtual/` deve conter:
- Todos os arquivos de configuração do nível raiz (pyproject.toml, README.md, etc.)
- Diretórios auxiliares completos (deployment/, eval/, tests/)
- Um log JSON detalhado com todas as operações realizadas

## Observação

O arquivo AGENTS.md foi atualizado com as novas fases. Siga rigorosamente as instruções das FASES 0 e 5 para completar a migração.