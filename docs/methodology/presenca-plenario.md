# Presença em sessões deliberativas do Plenário (Câmara)

**O que mede.** Em quantas sessões deliberativas do Plenário da Câmara, realizadas enquanto a pessoa estava no cargo, há registro de presença dela.

**Como é calculado.**

- **Sessões consideradas:** eventos do Plenário (órgão 180) do tipo "Sessão Deliberativa" (código 110) com situação "Encerrada", ou seja, sessões que de fato aconteceram.
- **Presença:** a lista oficial de deputados que registraram presença em cada sessão.
- **Valor:** sessões com presença registrada ÷ sessões realizadas nos dias em que a pessoa estava no cargo.
- **Licenças:** os dias de licença no período aparecem ao lado do resultado.

**Senado.** As APIs do Senado consultadas não trazem lista de presença por senador nas sessões. Por isso esta métrica aparece como "Ainda não disponível" para senadores.

**Fontes.** Câmara: `/eventos?idOrgao=180&codTipoEvento=110` e `/eventos/{id}/deputados`.
