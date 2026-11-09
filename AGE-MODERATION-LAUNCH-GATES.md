# Sintonia — gates de idade, segurança e moderação (proposta; não aprovação de lançamento)

**Estado: checklist para revisão independente. Não é parecer jurídico, avaliação de impacto, implementação ou evidência de conformidade. Não autoriza abrir cadastro, descoberta, curtidas ou chat.** Elaborado em 2026-11-09 com base nas fontes oficiais listadas ao final; confirmar versão e interpretação com assessoria jurídica e responsável de privacidade antes de qualquer lançamento.

## 1) Decisão de escopo e idade

- Tratar o Sintonia como serviço de relacionamento destinado a adultos, mas não presumir que uma etiqueta “18+”, uma data de nascimento autodeclarada ou a ausência de marketing infantil eliminam obrigações relativas a crianças/adolescentes. Avaliar o produto real, sua atratividade, facilidade de acesso, riscos e probabilidade de uso infantojuvenil segundo orientação vigente da ANPD.
- **Bloqueador:** definir com jurídico/privacidade uma aferição de idade confiável e proporcional antes de ativar cadastro, descoberta ou mensagens. Não aceitar autodeclaração de aniversário como garantia única.
- Documentar o método aprovado, fornecedor/indicador, limiar e tratamento de falha, falso positivo e recurso. Preferir um sinal de faixa/maioridade (“18+”) a cópia/retenção de documento, se tecnicamente e juridicamente adequado. Não guardar documento ou imagem facial por padrão; justificar necessidade, base legal, prazo, acesso, descarte e auditoria se qualquer dado de alta sensibilidade for inevitável.
- Bloquear o acesso a funcionalidades de relacionamento enquanto o resultado for “menor”, incerto ou indisponível. Criar fluxo seguro de contestação que não exponha perfil, contato ou dados privados. Não revelar ao usuário como contornar controles.
- Testar cenários: menor declarado; idade incerta; sinal ausente/inconsistente; conta já criada; troca de dispositivo/conta; falsificação/replay; tentativa repetida; pessoa adulta erroneamente bloqueada; exclusão do dado de verificação; suporte/contestação.
- Separar evidência de idade de data de nascimento pública: perfil e descoberta nunca devem expor data completa de nascimento, documento, sinal bruto ou dados de biometria. Registrar apenas o mínimo necessário para demonstrar a decisão e sua validade, com retenção definida.

## 2) Segurança e privacidade antes da interação entre usuários

- Revalidar em staging fiel o schema, owners, RLS, grants (incluindo PUBLIC), todas as funções/overloads, wrappers PostgREST, views, storage, triggers e caminhos diretos; testar como anon, conta A, conta B e terceiro C.
- Manter sem acesso de cliente as rotas reais de descoberta, curtida, lista/leitura/envio de conversa e qualquer caminho equivalente até aprovação do backend. A pausa da interface não substitui ACL/RLS.
- Aprovar e provar a regra de revogação: após ocultar/bloquear e commit, novas decisões de autorização não retornam conteúdo nem aceitam envio; curtidas, matches e mensagens continuam armazenados conforme decisão de produto. Documentar o limite de resposta já autorizada/in-flight e testar o cliente descartando respostas antigas.
- Verificar sessão, recuperação/alteração de senha, rate limits, proteção contra enumeração, abuso automatizado, XSS/injeção, upload e storage privado, logs sem segredos, no-store e acesso mínimo. Rodar revisão independente; guardar versões e evidências de cada teste.
- Definir inventário e fluxo de dados, finalidades/bases legais, retenção e eliminação, fornecedores/subprocessadores, atendimento a direitos, controle de acesso interno e plano de incidentes. Avaliar necessidade de Relatório de Impacto à Proteção de Dados (RIPD) com encarregado/jurídico; não presumir que este documento o substitua.

## 3) Operação de moderação antes de qualquer curtida/chat

- Designar responsável operacional e substituto, canais acessíveis para denúncia e recurso, cobertura/horários reais, treinamento e procedimento de escalonamento. Não anunciar resposta imediata ou cobertura 24/7 sem capacidade comprovada.
- Operar denúncias de perfil, assédio, fraude/golpe, ameaça, suspeita de menor e conteúdo/imagem não consentidos. Cada denúncia precisa gerar protocolo, confirmação, estado, trilha de auditoria, prazo interno, responsável e resultado comunicado com segurança.
- Implementar bloqueio que interrompa novas interações entre as partes, sem apagar automaticamente o histórico retido; validar comportamento de desbloqueio, reentrada e bloqueio recíproco. Minimizar exposição do denunciante ao denunciado.
- Criar matriz de gravidade e resposta, inclusive risco iminente à vida, ameaça/violência, exploração sexual e suspeita de menor. Preservação/divulgação de dados somente sob processo autorizado e orientação jurídica; não prometer sigilo absoluto nem fazer divulgação improvisada.
- Fixar prazos-alvo de triagem, escalonamento e decisão que a equipe consegue cumprir; testar simulações com casos sintéticos, falsos positivos, denúncia maliciosa e fila sobrecarregada. Registrar métricas sem expor dados pessoais desnecessários.
- Publicar regras comunitárias e política de moderação em linguagem clara; explicar o que é monitorado, como denunciar, quais ações podem ser tomadas, como recorrer e quais são os limites do serviço.

## 4) Evidência de aceite obrigatória

Cada gate só pode ser marcado **PASS** com artefato datado, responsável, versão e evidência reproduzível; promessa, código não executado ou teste unitário não contam como prova de ambiente real.

| Gate | Evidência exigida | Estado neste registro |
|---|---|---|
| Escopo ECA Digital e análise jurídica | Parecer/decisão assinada sobre aplicabilidade, deveres, idade e riscos do produto concreto | ABERTO |
| Idade confiável e minimizada | Método avaliado, teste de falhas/recursos, fluxo de descarte e revisão de privacidade | ABERTO |
| Schema/RLS/ACL e endpoints | Auditoria read-only exata + testes PostgREST autenticados em staging fiel, anon/A/B/C | ABERTO |
| Revogação e concorrência | Testes determinísticos de duas sessões, locks/barreiras observáveis e respostas HTTP reais | ABERTO |
| Segurança de conta e armazenamento | Testes de sessão, recuperação, limites, upload e acesso privado; revisão independente | ABERTO |
| Moderação operacional | Donos, canal real, cobertura, SLAs honestos, playbooks, simulações e escalonamento | ABERTO |
| Privacidade, retenção e incidentes | Inventário, avisos/termos, retenção/eliminações, RIPD se indicado, resposta a incidentes | ABERTO |
| Acessibilidade e lançamento | Testes E2E/acessibilidade, plano de reversão, monitoramento e aprovação explícita separada | ABERTO |

## 5) Estado factual e limites

- A UI local e a proposta têm testes frontend sintéticos; isso não prova segurança do Supabase/PostgREST nem conformidade legal.
- Não há, neste registro, evidência de ambiente staging fiel, de mecanismo de idade implantado, nem de operação real de denúncias/moderação.
- A proposta pública permanece em rascunho; nada neste checklist deve ser interpretado como autorização para merge, deploy ou mudança de permissões.
- Decisão atual: **NÃO PRONTO / manter fechado**. Não ativar signup, descoberta, curtidas ou chat enquanto todos os gates acima não tiverem evidência e aprovação apropriadas.

## Fontes oficiais consultadas (2026-11-09)

- [Lei nº 15.211/2025 — ECA Digital (Planalto)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15211.htm)
- [Guia da ANPD sobre escopo e responsabilidades dos fornecedores (28 out. 2026)](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-publica-guia-que-esclarece-quem-deve-cumprir-e-quais-sao-as-responsabilidades-das-plataformas-na-protecao-de-criancas-e-adolescentes)
- [Orientações preliminares da ANPD para aferição de idade (20 mar. 2026)](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-publica-orientacoes-preliminares-e-cronograma-para-afericao-de-idade-no-ambiente-digital)
- [Lei nº 13.709/2018 — LGPD (Planalto)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

O Planalto bloqueou a leitura automatizada direta durante esta revisão; as referências às leis servem para consulta pelo responsável jurídico, e não para interpretação jurídica automatizada. A análise factual sobre as orientações da ANPD foi feita com as páginas oficiais da própria ANPD acima.
