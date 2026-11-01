// All user-facing text, in Brazilian Portuguese (decision 0003). Owned by the technical writer;
// wording reviewed and approved by the project owner for neutrality on 2026-11-01 (task C4).
// A test checks this file against docs/wording/banned-pt-BR.txt.

export const text = {
  appName: "Placar Parlamentar",
  tagline:
    "Atividade pública de deputados e senadores federais, a partir de dados abertos oficiais da Câmara dos Deputados e do Senado Federal.",
  nav: { officials: "Parlamentares", compare: "Comparar", parties: "Partidos", methodology: "Metodologia" },
  snapshot: (date: string) => `Dados oficiais coletados em ${date}.`,
  noSnapshot: "Os dados ainda não foram carregados.",
  loading: "Carregando…",
  loadError: "Não foi possível carregar os dados.",
  notAvailableYet: "Ainda não disponível",
  notInOfficialData: "Não disponível nos dados oficiais",
  insufficientData: "Dados insuficientes",
  sourceShort: "Fonte",
  moreSources: (n: number) => `mais ${n.toLocaleString("pt-BR")} ${n === 1 ? "fonte" : "fontes"}`,
  notFoundTitle: "Página não encontrada",
  backHome: "Voltar ao início",

  filters: {
    period: "Período",
    presets: { legislatura: "Legislatura atual", "2anos": "Últimos 2 anos", personalizado: "Personalizado" },
    start: "Início",
    end: "Fim",
    threshold: "Mínimo de tempo no cargo",
    mode: { proporcao: "% do período", dias: "dias" },
    house: "Casa",
    allHouses: "Câmara e Senado",
    houses: { CAMARA: "Câmara dos Deputados", SENADO: "Senado Federal" } as Record<string, string>,
    state: "UF",
    party: "Partido",
    search: "Buscar por nome",
    apply: "Aplicar",
  },

  window: (start: string, end: string, days: string) => `Período: ${start} a ${end} (${days} dias).`,
  thresholdShare: (pct: string) => `Mínimo para comparação: ${pct} do período no cargo.`,
  thresholdDays: (days: string) => `Mínimo para comparação: ${days} dias no cargo.`,

  officials: {
    title: "Parlamentares",
    columns: { name: "Nome", house: "Casa", state: "UF", party: "Partido", days: "Dias no cargo", share: "Cobertura", status: "Situação" },
    sufficient: "Dados suficientes",
    notInOffice: (n: number) =>
      `${n} ${n === 1 ? "pessoa" : "pessoas"} da lista sem exercício no período ${n === 1 ? "não aparece" : "não aparecem"} acima.`,
    total: (n: number) => `${n} ${n === 1 ? "parlamentar" : "parlamentares"}`,
    previous: "Anterior",
    next: "Próxima",
    compareSelected: "Comparar selecionados",
    select: (name: string) => `Selecionar ${name} para comparar`,
  },

  official: {
    coverage: "Tempo no cargo no período",
    days: (d: string, total: string) => `${d} de ${total} dias`,
    periods: "Períodos de exercício",
    affiliations: "Filiação partidária",
    metrics: "Atividade no período",
    from: "Início",
    to: "Fim",
    ongoing: "em exercício",
    noEndDate: "sem data de fim no registro",
    startReason: "Motivo do início",
    endReason: "Motivo do fim",
    precisionAtEvent: "data conhecida apenas pelo registro do evento",
    insufficientNote: "O tempo no cargo neste período está abaixo do mínimo escolhido. Os números abaixo cobrem pouco tempo e podem não ser comparáveis aos de outras pessoas.",
  },

  metrics: {
    plenary_attendance: "Presença em sessões deliberativas do Plenário",
    bills_authored: "Proposições apresentadas (PL, PLP, PEC, PDL)",
    vote_participation: "Participação em votações nominais",
    speeches: "Discursos",
  } as Record<string, string>,
  metricValue: {
    ratio: (pct: string, n: string, d: string) => `${pct} (${n} de ${d})`,
    count: (n: string) => n,
    perYear: (v: string) => `${v} por 365 dias no cargo`,
    leaveDays: (n: string) => `Dias de licença no período: ${n}`,
    noneInPeriod: "Nenhum registro nos dias no cargo",
    presidedExcluded: (n: string) => `Votações presididas (não contadas): ${n}`,
  },

  summary: {
    title: "Resumo",
    template:
      "Texto gerado automaticamente a partir dos registros oficiais, com frases fixas preenchidas pelos dados.",
    model:
      "Texto gerado automaticamente por um modelo de linguagem a partir dos registros oficiais e conferido por regras antes de ser exibido.",
    howItIsMade: "Como o resumo é feito",
  },

  compare: {
    title: "Comparação",
    hint: "Escolha de 2 a 6 parlamentares na lista para comparar.",
    metric: "Métrica",
  },

  parties: {
    title: "Partidos",
    columns: {
      party: "Partido",
      inWindow: "Membros no período",
      atStart: "No início",
      atEnd: "No fim",
      sufficient: "Com dados suficientes",
    },
    changed: "Composição mudou no período",
    aggregateNote: "Mediana (mínimo–máximo) entre membros com dados suficientes; proposições e discursos por 365 dias no cargo.",
  },

  reasons: {
    ELECTED_OATH: "Posse de eleito titular",
    ALTERNATE_OATH: "Posse de suplente",
    ALTERNATE_AS_TITULAR: "Posse de suplente como titular",
    RETURN: "Reassunção",
    MESA_DECISION: "Decisão da Mesa",
    NOT_GIVEN: "Não informado pela fonte",
    TERM_END: "Término do mandato ou da legislatura",
    RESIGNATION: "Renúncia",
    DEATH: "Falecimento",
    LOSS_OF_MANDATE: "Perda ou cassação do mandato",
    LEAVE: "Licença",
    EXECUTIVE_OFFICE: "Afastamento para cargo no Executivo",
    TITULAR_RETURNED: "Retorno do titular",
    SUSPENSION: "Suspensão",
    COURT_DECISION: "Decisão judicial",
    RECOUNT: "Recontagem ou retotalização de votos",
    OTHER_ABSENCE: "Outro afastamento",
    UNKNOWN: "Não classificado",
    "": "—",
  } as Record<string, string>,

  methodology: {
    title: "Metodologia",
    intro:
      "Todos os números vêm das APIs de Dados Abertos da Câmara dos Deputados e do Senado Federal e têm link para o registro oficial. As métricas contam apenas os dias em que a pessoa estava no cargo dentro do período escolhido.",
    items: [
      "Tempo no cargo: períodos de exercício informados pelo Senado e montados a partir do histórico oficial da Câmara; dias contados no horário de Brasília, incluindo o primeiro e o último dia.",
      "Presença (Câmara): sessões deliberativas do Plenário com presença registrada, divididas pelas sessões realizadas nos dias no cargo. O Senado não publica lista de presença por senador nas APIs consultadas.",
      "Proposições: PL, PLP, PEC e PDL com a pessoa entre os autores, inclusive coautoria; também por 365 dias no cargo.",
      "Votações nominais: votações com voto registrado (Sim, Não, Abstenção, Obstrução), divididas pelas votações nominais realizadas nos dias no cargo, sem contar as secretas nem as que a pessoa presidiu.",
      "Discursos: pronunciamentos registrados nos dias no cargo; também por 365 dias no cargo.",
      "Dias de licença (Câmara): mostrados ao lado da presença, com a fonte oficial de cada licença.",
      "Quem fica abaixo do mínimo de tempo no cargo aparece como “Dados insuficientes”, com o período coberto.",
      "Por 365 dias no cargo: o total dividido pelos dias no cargo dentro do período e multiplicado por 365, para comparar pessoas com tempos diferentes no cargo.",
    ],
    summariesTitle: "Resumos",
    summaries: [
      "O resumo de cada parlamentar é escrito automaticamente a partir de uma lista de fatos montada com os mesmos números desta página (tempo no cargo, partidos e métricas), cada fato com sua fonte oficial. Textos de proposições ou discursos não são usados.",
      "Cada frase mostra as fontes dos fatos que usa. Antes de ser exibido, o texto passa por regras automáticas: toda frase cita fatos existentes; todo número, data, nome e partido aparece nesses fatos; nenhum termo da lista de palavras de julgamento vetadas; no máximo 6 frases de até 200 caracteres.",
      "Resumo por frases fixas: modelo de texto preenchido pelos dados; é o padrão e o único para períodos personalizados.",
      "Resumo por modelo de linguagem: gerado com antecedência para os períodos pré-definidos, apenas quando passa nas mesmas regras. Se não passar, ou se os dados mudarem, o resumo por frases fixas é exibido.",
    ],
  },
} as const;
