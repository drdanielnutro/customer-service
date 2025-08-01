# Dúvida:
2. Tipo de Retorno de save_artifact

  Minha interpretação: O método save_artifact retorna um INTEGER representando o número da versão (0, 1, 2...).

  Código em questão:
  return {
      "success": True,
      "version": "v1",  # Retornando string "v1"
  }

  Pergunta: Está incorreto retornar a versão como string "v1"? O ADK espera que seja retornado como integer (1)?

  # Resposta:
  1. Introdução ao Método save_artifact
O método save_artifact é uma funcionalidade central dentro da API Python do ADK, projetada para gerenciar dados binários. github.io A documentação oficial descreve os artefatos como um mecanismo para o gerenciamento de dados binários nomeados e versionados, que podem ser associados a uma única sessão de interação do usuário ou persistir através de múltiplas sessões. github.io O versionamento é um componente crucial, pois o sistema cria automaticamente uma nova versão cada vez que um artefato com o mesmo nome de arquivo é salvo. github.io Essa funcionalidade garante um rastreamento robusto e a capacidade de recuperar estados de dados anteriores.

2. Análise do Dicionário de Retorno
A investigação inicial buscou analisar a estrutura de um dicionário retornado pelo método save_artifact, especificamente para determinar o tipo de dado da chave 'version'. No entanto, a pesquisa na documentação revelou que o método não retorna uma estrutura de dados complexa como um dicionário ou um objeto personalizado. A documentação é explícita ao afirmar que o valor de retorno é, na verdade, um único número de versão. github.io Portanto, não há um dicionário para dissecar; o retorno da função é o próprio número da versão, e este valor é do tipo inteiro. github.io

3. Evidências da Documentação e Exemplos de Código
As evidências concretas extraídas da documentação oficial do ADK confirmam a natureza do valor de retorno do método save_artifact. A documentação afirma de forma inequívoca: "O método save_artifact retorna o número da versão inteiro que foi atribuído ao artefato recém-salvo." github.io O sistema de versionamento automático do ADK gerencia as versões de forma sequencial. github.io

Embora os exemplos de código na documentação demonstrem como chamar callback_context.save_artifact, eles nem sempre capturam e utilizam o valor de retorno diretamente. github.io github.com No entanto, a documentação textual que acompanha os exemplos esclarece o comportamento. Ela explica como o número de versão inteiro retornado pode ser usado posteriormente para recuperar uma versão específica de um artefato, utilizando o método load_artifact(..., version=N), onde N é o número inteiro da versão desejada. github.io

4. Conclusão: O Tipo de Dado Correto para a Versão
Com base nas evidências coletadas na documentação oficial do ADK, a resposta definitiva é que o valor de retorno do método save_artifact é um inteiro. github.io Este inteiro representa o número da versão do artefato que acabou de ser salvo. github.io Consequentemente, uma implementação que retorna a versão como uma string (por exemplo, "v1") está em desacordo com a especificação da API. A prática correta é que a função retorne o número da versão como um tipo de dado inteiro, que é atribuído sequencialmente pelo sistema de versionamento do ADK.