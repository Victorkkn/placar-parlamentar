# Participação em votações nominais

**O que mede.** Em quantas votações nominais e não secretas do Plenário, realizadas enquanto a pessoa estava no cargo, há um voto registrado por ela.

**Como é calculado.**

- **Conta como participação** um voto registrado: Sim, Não, Abstenção ou Obstrução.
- **Votações presididas** pela pessoa (Câmara: "Artigo 17"; Senado: "Presidente (art. 51 RISF)") ficam fora da conta.
- **Ausências com motivo oficial** (por exemplo, "Atividade parlamentar" ou tipos de licença, conforme a tabela oficial do Senado) aparecem separadas e não contam como participação.
- **Valor:** votações com voto registrado ÷ votações nominais realizadas nos dias no cargo, menos as presididas.
- **Na Câmara,** a lista oficial traz apenas quem registrou voto. No Senado, traz todos os senadores, com o tipo de comparecimento.
- **Votações secretas** ficam fora da conta. No Senado, a fonte marca a votação como secreta. Na Câmara, que não tem essa marcação, uma votação em que todos os votos registrados vêm sem a opção é tratada como secreta.
- Opções de voto que não constam das listas acima aparecem como "Não classificado" e são informadas, nunca adivinhadas.

**Esta métrica não é presença.** Ela mede apenas o registro de voto nas votações nominais.

**Fontes.** Câmara: `/votacoes?idOrgao=180` e `/votacoes/{id}/votos`. Senado: `/votacao` e `/plenario/lista/tiposComparecimento`.
