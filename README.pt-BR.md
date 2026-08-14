# Global Builder Opportunity Radar

Radar local para reunir freelas, contratos por projeto, grants, hackathons premiados, programas
pagos e bounties em um banco SQLite deduplicado e classificado para o perfil do usuário.

Também procura projetos de marketing, CRM, geração de leads, Sales Ops, RevOps, conteúdo,
relatórios e atendimento nos quais automação possa ser usada como serviço ou diferencial.

O objetivo é encontrar renda alternativa fora do emprego tradicional. Wellfound e InfoJobs já
cobrem a busca por emprego; vagas permanentes comuns não pertencem ao resultado principal deste
projeto.

O radar monitora Reddit, Hacker News, sinais relacionados à Algora no GitHub, Opire e Superteam
Earn. APIs e RSS são priorizados;
Scrapling atende páginas públicas e dinâmicas; Apify será usado quando oferecer vantagem real de
proxy, execução em nuvem ou Actor existente.

O projeto não envia mensagens nem candidaturas. Primeiro ele prova a qualidade da coleta e mantém
um histórico verificável das oportunidades encontradas.

O ranking favorece bounties, freelas, automação, Python, scraping e contatos diretos. Para ver
somente oportunidades pagas com descrição e link completos:

```powershell
python -X utf8 radar.py report --paid-only --format detailed --limit 10
```

Consulte o [README principal](README.md) para instalação, arquitetura e comandos.
