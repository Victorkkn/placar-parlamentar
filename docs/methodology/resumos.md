# Resumos

**O que é.** Um texto curto sobre a atividade pública da pessoa no período escolhido, escrito automaticamente a partir dos mesmos números da página. Cada frase mostra as fontes oficiais dos fatos que usa.

**De onde vêm os fatos.** Uma lista de fatos montada a partir dos registros oficiais: tempo no cargo, partidos no período e as métricas disponíveis (presença, proposições, votações nominais, discursos). Cada fato tem sua fonte. Textos de proposições ou de discursos não são usados.

**Regras conferidas antes de exibir.** O texto inteiro é descartado se alguma regra falhar:

- toda frase cita pelo menos um fato existente, com fonte oficial;
- todo número e toda data da frase aparecem nos fatos citados;
- todo nome de pessoa ou de partido aparece nos fatos citados;
- nenhum termo da lista de termos vetados (`docs/wording/banned-pt-BR.txt`);
- no máximo 6 frases, cada uma com até 200 caracteres.

**Dois tipos de resumo.**

- **Frases fixas** (padrão): um modelo de texto preenchido pelos dados. É o único tipo para períodos personalizados.
- **Modelo de linguagem**: gerado com antecedência para os períodos pré-definidos (legislatura atual e últimos 2 anos), apenas quando passa nas regras acima. Se não passar, ou se os dados mudarem depois, o resumo por frases fixas é exibido. A página informa qual dos dois tipos está sendo mostrado.
