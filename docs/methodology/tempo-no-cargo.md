# Tempo no cargo e cobertura

**O que mede.** Quantos dias, dentro do período escolhido, a pessoa estava em exercício do mandato, e que parte do período isso representa (cobertura).

**Como é calculado.**

- **Senado:** usamos os períodos de exercício (`Exercicios`) informados pelo Senado para cada mandato.
- **Câmara:** montamos os períodos a partir do histórico oficial de cada deputado ou deputada: um registro de "Entrada" abre um período e um registro de "Saída" o encerra. Decisões da Mesa sobre recontagem ou retotalização de votos e sobre restabelecimento do mandato também abrem ou encerram períodos, conforme o texto do registro.
- Os dias são contados no horário de Brasília, incluindo o primeiro e o último dia. Períodos que se sobrepõem são unidos, para que nenhum dia conte duas vezes.
- A data de uma "Saída" conta como último dia no cargo.
- Cobertura = dias no cargo ÷ dias do período escolhido.

**Licenças.**

- No Senado, uma licença curta sem convocação de suplente não interrompe o exercício, e esses dias contam como tempo no cargo.
- Na Câmara, uma "Saída" por licença encerra o período, porque o suplente assume a vaga.
- Em ambos os casos, os dias de licença aparecem separados, ao lado da presença.

**Limites conhecidos.**

- Alguns registros de "Saída" da Câmara têm horário 00:00 em vez de 23:59, o que pode acrescentar um dia.
- A mesma pessoa que foi deputada e depois senadora aparece como dois registros separados, porque as fontes não trazem um identificador comum.

**Fontes.** Câmara: `/deputados/{id}/historico`. Senado: `/senador/{codigo}/mandatos` e `/senador/{codigo}/licencas`.
